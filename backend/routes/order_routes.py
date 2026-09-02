from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g, current_app
from backend.models.models import (
    db, Cart, CartItem, Food, Combo, Customer, Restaurant, Order, OrderItem, Payment, Notification,
    OrderTrackingEvent,
)
from backend.middleware.auth_middleware import token_required
from backend.services.wallet_service import debit_wallet
from backend.services.authority_service import require_permission, has_permission
from backend.services.pricing_service import effective_food_price, effective_combo_price, register_deal_usage
from backend.services import loyalty_service
from backend.services import referral_service
from backend.services import pass_service
from backend.services import promotion_service
from backend.services import tipping_service


def _iso_utc(dt):
    """Serialize a naive UTC datetime (everything in this app is stored via
    datetime.utcnow()) with an explicit 'Z' suffix.

    Without this, `dt.isoformat()` produces a string with no timezone info
    (e.g. "2026-08-28T05:12:00"). JavaScript's `new Date(...)` treats a
    string like that as *local* time rather than UTC, so the browser never
    applies the person's actual UTC offset and displays the raw UTC clock
    reading as if it were already local -- which is why the "Timeline"
    times looked hours off from the "Live — updated ..." time (which comes
    from `new Date()` in the browser and is correctly local). Appending
    "Z" tells the browser this is UTC, so it converts to local time
    correctly everywhere it's displayed.
    """
    if dt is None:
        return None
    return dt.isoformat() + "Z"


def validate_and_price_cart_items(cart_items):
    """
    Shared core of checkout validation, used by direct cart checkout,
    Scheduled Order conversion, and One-Tap Reorder alike, so every path
    re-validates availability/stock/price identically and server-side.

    Returns (subtotal: float, restaurant_id: int, line_specs: list) on
    success, or raises ValueError(message) with a customer-facing reason.
    line_specs is a list of dicts ready to become OrderItem rows, and also
    carries the inventory/flash-sale side effects to apply on commit.
    """
    subtotal = 0.0
    restaurant_id = None
    line_specs = []

    for ci in cart_items:
        if ci.food_id:
            food = Food.query.get(ci.food_id)
            if not food or not food.is_available:
                raise ValueError(f"'{food.name if food else 'Item'}' is no longer available.")
            if restaurant_id is None:
                restaurant_id = food.restaurant_id
            elif restaurant_id != food.restaurant_id:
                raise ValueError("Cart contains items from multiple restaurants.")
            if food.track_inventory:
                available = food.stock_quantity or 0
                if ci.quantity > available:
                    raise ValueError(f"'{food.name}' only has {available} left in stock.")
            price, flash_sale = effective_food_price(food)
            line_total = round(price * ci.quantity, 2)
            subtotal += line_total
            line_specs.append({
                "food_id": food.id, "combo_id": None, "food_name": food.name,
                "unit_price": price, "quantity": ci.quantity, "line_total": line_total,
                "decrement_stock": food if food.track_inventory else None,
                "deal_info": flash_sale,
            })

        elif ci.combo_id:
            combo = Combo.query.get(ci.combo_id)
            if not combo or not combo.is_currently_active():
                raise ValueError(f"'{combo.name if combo else 'Combo'}' is no longer available.")
            if restaurant_id is None:
                restaurant_id = combo.restaurant_id
            elif restaurant_id != combo.restaurant_id:
                raise ValueError("Cart contains items from multiple restaurants.")
            price, flash_sale = effective_combo_price(combo)
            line_total = round(price * ci.quantity, 2)
            subtotal += line_total
            line_specs.append({
                "food_id": None, "combo_id": combo.id, "food_name": f"Combo: {combo.name}",
                "unit_price": price, "quantity": ci.quantity, "line_total": line_total,
                "decrement_stock": None,
                "deal_info": flash_sale,
            })
        else:
            continue

    if not line_specs:
        raise ValueError("Cart is empty or contains no valid items.")

    return round(subtotal, 2), restaurant_id, line_specs


def apply_line_specs_to_order(order, line_specs):
    """Creates OrderItem rows and applies the inventory/flash-sale side
    effects computed by validate_and_price_cart_items(). Call after
    order.id exists (post-flush) and before commit."""
    for spec in line_specs:
        db.session.add(OrderItem(
            order_id=order.id, food_id=spec["food_id"], combo_id=spec["combo_id"],
            food_name=spec["food_name"], unit_price=spec["unit_price"],
            quantity=spec["quantity"], line_total=spec["line_total"],
        ))
        if spec["decrement_stock"] is not None:
            food = spec["decrement_stock"]
            food.stock_quantity = max(0, (food.stock_quantity or 0) - spec["quantity"])
            if food.stock_quantity == 0:
                food.is_available = False
        if spec["deal_info"]:
            register_deal_usage(spec["deal_info"], spec["quantity"])


order_bp = Blueprint("order", __name__, url_prefix="/api/orders")


@order_bp.route("/tip-suggestions", methods=["GET"])
@token_required(["customer"])
def get_tip_suggestions():
    try:
        subtotal = float(request.args.get("subtotal", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "subtotal must be a number."}), 400
    return jsonify({
        "suggestions": tipping_service.suggest_tips(subtotal),
        "note": "Suggested based on your order amount. Tipping is always optional.",
    }), 200

VALID_TRANSITIONS = {
    "placed": {"accepted", "cancelled"},
    "accepted": {"preparing", "cancelled"},
    "preparing": {"ready", "cancelled"},
    "ready": {"out_for_delivery"},
    "out_for_delivery": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}

# Automatic delivery: any active (non-cancelled, non-delivered) order is
# considered delivered once this many seconds have passed since it was
# placed. The database's own created_at timestamp is always the source of
# truth for this calculation -- never a browser timer -- so the result is
# correct no matter when/how often the order is subsequently fetched.
AUTO_DELIVER_SECONDS = 120


def _auto_progress_if_due(order: Order) -> bool:
    """
    If enough time has elapsed since the order was placed, mark it delivered
    (and settle COD payment the same way a manual 'delivered' transition
    would). Returns True if the order was changed so callers know to commit.
    Cancelled orders, and orders already delivered, are left untouched.
    """
    if order.order_status in ("delivered", "cancelled"):
        return False
    if order.created_at is None:
        return False

    elapsed = datetime.utcnow() - order.created_at
    if elapsed < timedelta(seconds=AUTO_DELIVER_SECONDS):
        return False

    order.order_status = "delivered"
    if order.payment_method == "cod":
        order.payment_status = "paid"
        payment = Payment.query.filter_by(order_id=order.id, method="cod").first()
        if payment:
            payment.status = "success"
    db.session.add(OrderTrackingEvent(order_id=order.id, status="delivered", note="Auto-marked delivered."))
    # Award loyalty points now that the order is genuinely delivered & paid.
    # award_points_for_order() is idempotent (unique constraint on
    # reference_type+reference_id+transaction_type), so this is always safe
    # to call even if this order somehow gets re-checked later.
    loyalty_service.award_points_for_order(order)
    referral_service.process_referral_if_qualified(order)
    return True


def _serialize_order(o: Order):
    from backend.models.models import DeliveryBenefitUsage, OrderPackingProof
    benefit = DeliveryBenefitUsage.query.filter_by(order_id=o.id).first()
    has_packing_proof = OrderPackingProof.query.filter_by(order_id=o.id).first() is not None
    return {
        "id": o.id,
        "customer_id": o.customer_id,
        "customer_name": f"{o.customer.first_name} {o.customer.last_name}" if o.customer else None,
        "restaurant_id": o.restaurant_id,
        "restaurant_name": o.restaurant.restaurant_name if o.restaurant else None,
        "address": o.address_text,
        "subtotal": float(o.subtotal),
        "discount_amount": float(o.discount_amount),
        "delivery_fee": float(o.delivery_fee),
        "delivery_fee_waived_by_pass": float(benefit.discount_amount) if benefit else 0,
        "tip_amount": float(o.tip_amount or 0),
        "eco_delivery": bool(o.eco_delivery),
        "donation_amount": float(o.donation_amount or 0),
        "total_amount": float(o.total_amount),
        "payment_method": o.payment_method,
        "payment_status": o.payment_status,
        "order_status": o.order_status,
        "delivery_instruction": o.delivery_instruction,
        "has_packing_proof": has_packing_proof,
        "created_at": _iso_utc(o.created_at),
        "items": [{
            "food_id": i.food_id, "combo_id": i.combo_id, "food_name": i.food_name,
            "unit_price": float(i.unit_price), "quantity": i.quantity, "line_total": float(i.line_total),
        } for i in o.items],
    }


@order_bp.route("", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.place_order")
def create_order():
    """Checkout: creates order from the customer's cart. Razorpay orders are
    created but marked payment_status=pending until verified (see payment_routes).
    COD orders are placed immediately with payment_status=pending.
    Wallet orders are debited server-side and marked paid immediately."""
    data = request.get_json(force=True) or {}
    payment_method = data.get("payment_method")
    address_text = data.get("address")
    address_id = data.get("address_id")  # optional: id of a saved Address, for structured location snapshotting

    if payment_method not in ("razorpay", "cod", "wallet"):
        return jsonify({"error": "Invalid payment method."}), 400
    if not address_text:
        return jsonify({"error": "Delivery address is required."}), 400

    customer = Customer.query.filter_by(user_id=g.user_id).first()

    # If the customer checked out with a saved address, snapshot its
    # structured location (city/pincode/coordinates) onto the order for
    # aggregate admin analytics (Order Heatmap). Ownership-checked -- a
    # customer can only snapshot from their OWN saved address.
    delivery_city_id = delivery_pincode = delivery_latitude = delivery_longitude = None
    delivery_instruction = data.get("delivery_instruction")  # allows override even without a saved address
    if address_id:
        from backend.models.models import Address
        saved_address = Address.query.filter_by(id=address_id, customer_id=customer.id).first()
        if saved_address:
            delivery_city_id = saved_address.city_id
            delivery_pincode = saved_address.pincode
            delivery_latitude = saved_address.latitude
            delivery_longitude = saved_address.longitude
            if not delivery_instruction:
                delivery_instruction = saved_address.delivery_instruction

    # Payment-method-specific authority: admin can disable individual
    # payment methods (COD / online payment / wallet) per customer even
    # while "Place Order" itself stays enabled.
    method_permission = {
        "cod": "customer.cod", "razorpay": "customer.online_payment", "wallet": "customer.wallet",
    }[payment_method]
    if not has_permission(customer.id, "customer", method_permission):
        return jsonify({"error": f"This payment method has been restricted by the administrator."}), 403
    cart = Cart.query.filter_by(customer_id=customer.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not cart_items:
        return jsonify({"error": "Your cart is empty."}), 400

    # revalidate availability, stock & price server-side (never trust client totals)
    try:
        subtotal, restaurant_id, line_specs = validate_and_price_cart_items(cart_items)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    delivery_fee = current_app.config["DELIVERY_FEE"]

    # QuickBite Pass: waive the delivery fee if an active, eligible pass
    # covers this order. Eligibility and usage counts are always re-checked
    # here server-side -- the frontend only ever displays the result.
    pass_benefit = pass_service.get_eligible_benefit(customer.id, restaurant_id, subtotal)
    delivery_fee_charged = 0 if pass_benefit else delivery_fee

    # Promotion A/B test: apply the customer's assigned variant discount
    # (if any experiment is currently running), always computed server-side.
    promo_discount, promo_assignment_id = promotion_service.get_order_discount(customer.id, subtotal)

    # Dynamic Tipping (optional, customer-chosen -- never forced) and
    # Post-Order Micro-Donations (optional round-up). Both are validated
    # server-side; the frontend only ever suggests, never dictates, a value.
    try:
        tip_amount = round(float(data.get("tip_amount", 0) or 0), 2)
        if tip_amount < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "tip_amount must be a non-negative number."}), 400

    donation_amount = 0.0
    if data.get("round_up_donation"):
        pre_donation_total = round(subtotal - promo_discount + (0 if pass_benefit else delivery_fee) + tip_amount, 2)
        donation_amount = round(-(-pre_donation_total // 1) - pre_donation_total, 2)  # round up to next whole rupee
        if donation_amount <= 0:
            donation_amount = 1.0  # already a whole number -- round up a full rupee instead of ₹0

    eco_delivery = bool(data.get("eco_delivery", False))

    total = round(subtotal - promo_discount + delivery_fee_charged + tip_amount + donation_amount, 2)

    VALID_DELIVERY_INSTRUCTIONS = {"silent_drop", "ring_bell", "call_me"}
    if delivery_instruction and delivery_instruction not in VALID_DELIVERY_INSTRUCTIONS:
        return jsonify({"error": "Invalid delivery_instruction."}), 400

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant_id,
        address_text=address_text,
        delivery_city_id=delivery_city_id,
        delivery_pincode=delivery_pincode,
        delivery_latitude=delivery_latitude,
        delivery_longitude=delivery_longitude,
        delivery_instruction=delivery_instruction,
        promotion_assignment_id=promo_assignment_id,
        subtotal=round(subtotal, 2),
        discount_amount=promo_discount,
        delivery_fee=delivery_fee_charged,
        tip_amount=tip_amount,
        eco_delivery=eco_delivery,
        donation_amount=donation_amount,
        total_amount=total,
        payment_method=payment_method,
        payment_status="pending",
        order_status="placed",
    )
    db.session.add(order)
    db.session.flush()

    if pass_benefit:
        pass_service.apply_benefit(pass_benefit, order.id, customer.id, delivery_fee)

    apply_line_specs_to_order(order, line_specs)
    db.session.add(OrderTrackingEvent(order_id=order.id, status="placed"))

    # Handle payment method specifics
    if payment_method == "wallet":
        try:
            debit_wallet(customer.id, total, f"Order #{order.id} payment", "order", order.id)
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
        order.payment_status = "paid"
        db.session.add(Payment(order_id=order.id, method="wallet", amount=total, status="success"))

    elif payment_method == "cod":
        order.payment_status = "pending"
        db.session.add(Payment(order_id=order.id, method="cod", amount=total, status="pending"))

    elif payment_method == "razorpay":
        order.payment_status = "pending"
        db.session.add(Payment(order_id=order.id, method="razorpay", amount=total, status="pending"))
        # Actual Razorpay order creation happens in /api/payments/razorpay/create-order

    # clear cart, notify restaurant
    CartItem.query.filter_by(cart_id=cart.id).delete()
    restaurant = Restaurant.query.get(restaurant_id)
    db.session.add(Notification(
        recipient_role="restaurant", recipient_id=restaurant.id,
        title="New Order Received", message=f"Order #{order.id} placed for ₹{total}.",
    ))
    db.session.add(Notification(
        recipient_role="customer", recipient_id=customer.id,
        title="Order Placed", message=f"Your order #{order.id} has been placed.",
    ))
    db.session.commit()

    from backend.services import streak_service
    streak_service.record_activity(customer.id, source="order")

    return jsonify(_serialize_order(order)), 201


@order_bp.route("/mine", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.view_orders")
def my_orders():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()

    # Backend is the source of truth for the 2-minute auto-delivery timer:
    # every time "My Orders" is loaded/refreshed/polled, check each active
    # order's actual created_at against the clock and persist any that are due.
    changed = False
    for o in orders:
        if _auto_progress_if_due(o):
            changed = True
    if changed:
        db.session.commit()

    return jsonify([_serialize_order(o) for o in orders]), 200


@order_bp.route("/restaurant", methods=["GET"])
@token_required(["restaurant"])
@require_permission("restaurant.view_orders")
def restaurant_orders():
    restaurant = Restaurant.query.filter_by(user_id=g.user_id).first()
    orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).all()
    return jsonify([_serialize_order(o) for o in orders]), 200


@order_bp.route("/<int:order_id>", methods=["GET"])
@token_required()
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found."}), 404

    # ownership check: customers see only their own, restaurants only their own, admin sees all
    if g.role == "customer":
        customer = Customer.query.filter_by(user_id=g.user_id).first()
        if order.customer_id != customer.id:
            return jsonify({"error": "Forbidden."}), 403
        if not has_permission(customer.id, "customer", "customer.track_order"):
            return jsonify({"error": "Order tracking has been restricted by the administrator."}), 403
    elif g.role == "restaurant":
        restaurant = Restaurant.query.filter_by(user_id=g.user_id).first()
        if order.restaurant_id != restaurant.id:
            return jsonify({"error": "Forbidden."}), 403

    if _auto_progress_if_due(order):
        db.session.commit()

    return jsonify(_serialize_order(order)), 200


STAGE_ORDER = ["placed", "accepted", "preparing", "ready", "out_for_delivery", "delivered"]


def _estimate_delivery_time(order):
    """Grounded ETA: order placement time + the slowest item's own
    preparation_time_minutes (real data set by the restaurant) + any current
    kitchen-load extra time the restaurant has flagged + a fixed delivery
    buffer. This is a real estimate derived from actual menu/kitchen data,
    not a fabricated countdown."""
    from backend.services import kitchen_service
    prep_minutes = 20
    if order.items:
        known = [i.food.preparation_time_minutes for i in order.items if i.food and i.food.preparation_time_minutes]
        if known:
            prep_minutes = max(known)
    kitchen_extra_minutes = kitchen_service.extra_minutes_for(order.restaurant_id)
    delivery_buffer_minutes = 25
    return order.created_at + timedelta(minutes=prep_minutes + kitchen_extra_minutes + delivery_buffer_minutes)


@order_bp.route("/<int:order_id>/tracking", methods=["GET"])
@token_required()
def get_order_tracking(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found."}), 404

    if g.role == "customer":
        customer = Customer.query.filter_by(user_id=g.user_id).first()
        if order.customer_id != customer.id:
            return jsonify({"error": "Forbidden."}), 403
        if not has_permission(customer.id, "customer", "customer.track_order"):
            return jsonify({"error": "Order tracking has been restricted by the administrator."}), 403
    elif g.role == "restaurant":
        restaurant = Restaurant.query.filter_by(user_id=g.user_id).first()
        if order.restaurant_id != restaurant.id:
            return jsonify({"error": "Forbidden."}), 403

    if _auto_progress_if_due(order):
        db.session.commit()

    events = OrderTrackingEvent.query.filter_by(order_id=order.id).order_by(OrderTrackingEvent.created_at.asc()).all()
    is_terminal = order.order_status in ("delivered", "cancelled")

    return jsonify({
        "order_id": order.id,
        "order_status": order.order_status,
        "restaurant_name": order.restaurant.restaurant_name if order.restaurant else None,
        "restaurant_address": order.restaurant.address if order.restaurant else None,
        "delivery_address": order.address_text,
        "items": [{"food_name": i.food_name, "quantity": i.quantity} for i in order.items],
        "stage_order": STAGE_ORDER,
        "estimated_delivery_time": _iso_utc(_estimate_delivery_time(order)) if not is_terminal else None,
        "timeline": [{
            "status": e.status, "note": e.note, "at": _iso_utc(e.created_at),
        } for e in events],
        "created_at": _iso_utc(order.created_at),
    }), 200


@order_bp.route("/<int:order_id>/cancel", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.cancel_order")
def customer_cancel_order(order_id):
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    order = Order.query.get(order_id)
    if not order or order.customer_id != customer.id:
        return jsonify({"error": "Order not found."}), 404

    allowed_next = VALID_TRANSITIONS.get(order.order_status, set())
    if "cancelled" not in allowed_next:
        return jsonify({"error": f"Order can no longer be cancelled (current status: '{order.order_status}')."}), 400

    order.order_status = "cancelled"
    if order.payment_status == "paid":
        order.payment_status = "refund_pending"
    db.session.add(OrderTrackingEvent(order_id=order.id, status="cancelled"))

    # If loyalty points were already awarded for this order (shouldn't
    # normally happen for a not-yet-delivered order, but handled safely
    # regardless), reverse them so refunds/cancellations never leave stale rewards.
    loyalty_service.reverse_points_for_order(order, reason=f"Order #{order.id} cancelled by customer")

    db.session.add(Notification(
        recipient_role="restaurant", recipient_id=order.restaurant_id,
        title="Order Cancelled", message=f"Order #{order.id} was cancelled by the customer.",
    ))
    db.session.commit()
    return jsonify(_serialize_order(order)), 200


@order_bp.route("/<int:order_id>/status", methods=["PUT"])
@token_required(["restaurant", "admin"])
def update_order_status(order_id):
    data = request.get_json(force=True) or {}
    new_status = data.get("status")

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found."}), 404

    if g.role == "restaurant":
        restaurant = Restaurant.query.filter_by(user_id=g.user_id).first()
        if order.restaurant_id != restaurant.id:
            return jsonify({"error": "Forbidden: not your order."}), 403

        # Fine-grained restaurant authority: which specific transition is
        # being attempted determines which permission is required.
        if new_status == "cancelled":
            required_perm = "restaurant.reject_order"
        elif new_status == "accepted":
            required_perm = "restaurant.accept_order"
        else:
            required_perm = "restaurant.update_order"
        if not has_permission(restaurant.id, "restaurant", required_perm):
            return jsonify({"error": "This action has been restricted by the administrator."}), 403

    allowed_next = VALID_TRANSITIONS.get(order.order_status, set())
    if new_status not in allowed_next:
        return jsonify({"error": f"Cannot transition from '{order.order_status}' to '{new_status}'."}), 400

    order.order_status = new_status
    db.session.add(OrderTrackingEvent(order_id=order.id, status=new_status))
    if new_status == "delivered" and order.payment_method == "cod":
        order.payment_status = "paid"
        payment = Payment.query.filter_by(order_id=order.id, method="cod").first()
        if payment:
            payment.status = "success"

    if new_status == "cancelled":
        loyalty_service.reverse_points_for_order(order, reason=f"Order #{order.id} cancelled/rejected")

    db.session.add(Notification(
        recipient_role="customer", recipient_id=order.customer_id,
        title="Order Update", message=f"Your order #{order.id} is now '{new_status.replace('_',' ')}'.",
    ))
    db.session.commit()

    # Award loyalty the moment an order reaches "delivered" via this manual
    # path too (idempotent -- award_points_for_order() no-ops if already awarded).
    if new_status == "delivered":
        loyalty_service.award_points_for_order(order)
        referral_service.process_referral_if_qualified(order)

    return jsonify(_serialize_order(order)), 200