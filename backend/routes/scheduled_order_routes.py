"""
Scheduled Orders. A customer books a future order (date/time/restaurant/
items/address/payment method). Conversion into a real Order happens
lazily -- the same "check due status whenever the customer's data is
fetched" pattern the existing Order auto-delivery logic already uses
(order_routes._auto_progress_if_due) -- rather than inventing a background
job scheduler this codebase has no infrastructure for.

Payment methods supported for scheduled orders: COD and Wallet only.
Razorpay is deliberately excluded -- an online payment requires the
customer to be present to complete an interactive checkout, which isn't
possible for an order that converts unattended in the future.
"""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, g

from backend.models.models import (
    db, Customer, Restaurant, Food, Order, Payment, Notification, ScheduledOrder, ScheduledOrderItem,
    OrderTrackingEvent,
)
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission, has_permission
from backend.services.wallet_service import debit_wallet
from backend.services.pricing_service import effective_food_price, register_flash_sale_usage

scheduled_order_bp = Blueprint("scheduled_order", __name__, url_prefix="/api/customer/scheduled-orders")

# A scheduled order can only be cancelled up until this long before its slot.
CANCELLATION_CUTOFF = timedelta(minutes=15)


def _serialize(so: ScheduledOrder):
    return {
        "id": so.id,
        "restaurant_id": so.restaurant_id,
        "restaurant_name": so.restaurant.restaurant_name if so.restaurant else None,
        "address": so.address_text,
        "payment_method": so.payment_method,
        "scheduled_for": so.scheduled_for.isoformat(),
        "status": so.status,
        "failure_reason": so.failure_reason,
        "created_order_id": so.created_order_id,
        "can_cancel": so.status == "scheduled" and (so.scheduled_for - datetime.utcnow()) > CANCELLATION_CUTOFF,
        "items": [
            {"food_id": i.food_id, "food_name": i.food.name if i.food else "Unknown item", "quantity": i.quantity}
            for i in so.items
        ],
        "created_at": so.created_at.isoformat() if so.created_at else None,
    }


def _convert_if_due(so: ScheduledOrder):
    """Attempts to turn a due scheduled order into a real Order. On any
    validation failure the scheduled order is marked 'failed' with a
    customer-visible reason -- it is never silently dropped or force-placed
    with stale data."""
    if so.status != "scheduled" or so.scheduled_for > datetime.utcnow():
        return False

    restaurant = Restaurant.query.get(so.restaurant_id)
    if not restaurant or restaurant.status != "approved":
        so.status, so.failure_reason = "failed", "Restaurant is no longer available."
        return True

    subtotal = 0.0
    line_specs = []
    for item in so.items:
        food = Food.query.get(item.food_id)
        if not food or not food.is_available or food.restaurant_id != so.restaurant_id:
            so.status = "failed"
            so.failure_reason = f"'{item.food.name if item.food else 'An item'}' is no longer available."
            return True
        if food.track_inventory and (food.stock_quantity or 0) < item.quantity:
            so.status = "failed"
            so.failure_reason = f"'{food.name}' no longer has enough stock."
            return True
        price, flash_sale = effective_food_price(food)
        line_total = round(price * item.quantity, 2)
        subtotal += line_total
        line_specs.append({
            "food": food, "quantity": item.quantity, "unit_price": price,
            "line_total": line_total, "flash_sale_id": flash_sale["flash_sale_id"] if flash_sale else None,
        })

    delivery_fee = 40.0  # matches Config.DELIVERY_FEE default; see note in create()
    total = round(subtotal + delivery_fee, 2)

    order = Order(
        customer_id=so.customer_id, restaurant_id=so.restaurant_id, address_text=so.address_text,
        subtotal=round(subtotal, 2), discount_amount=0, delivery_fee=delivery_fee, total_amount=total,
        payment_method=so.payment_method, payment_status="pending", order_status="placed",
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderTrackingEvent(order_id=order.id, status="placed", note="Placed from a scheduled order."))

    from backend.models.models import OrderItem
    for spec in line_specs:
        food = spec["food"]
        db.session.add(OrderItem(
            order_id=order.id, food_id=food.id, food_name=food.name,
            unit_price=spec["unit_price"], quantity=spec["quantity"], line_total=spec["line_total"],
        ))
        if food.track_inventory:
            food.stock_quantity = max(0, (food.stock_quantity or 0) - spec["quantity"])
            if food.stock_quantity == 0:
                food.is_available = False
        if spec["flash_sale_id"]:
            register_flash_sale_usage(spec["flash_sale_id"], spec["quantity"])

    if so.payment_method == "wallet":
        try:
            debit_wallet(so.customer_id, total, f"Scheduled order #{order.id} payment", "order", order.id)
            order.payment_status = "paid"
            db.session.add(Payment(order_id=order.id, method="wallet", amount=total, status="success"))
        except ValueError as e:
            db.session.rollback()
            so.status, so.failure_reason = "failed", str(e)
            db.session.commit()
            return True
    else:  # cod
        db.session.add(Payment(order_id=order.id, method="cod", amount=total, status="pending"))

    so.status = "completed"
    so.created_order_id = order.id

    db.session.add(Notification(
        recipient_role="customer", recipient_id=so.customer_id,
        title="Scheduled Order Placed", message=f"Your scheduled order is now Order #{order.id}.",
    ))
    db.session.add(Notification(
        recipient_role="restaurant", recipient_id=so.restaurant_id,
        title="New Order Received", message=f"Scheduled order #{order.id} placed for ₹{total}.",
    ))
    return True


@scheduled_order_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.scheduled_orders")
def list_scheduled_orders():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    orders = ScheduledOrder.query.filter_by(customer_id=customer.id).order_by(ScheduledOrder.scheduled_for.desc()).all()

    changed = False
    for so in orders:
        if _convert_if_due(so):
            changed = True
    if changed:
        db.session.commit()

    return jsonify([_serialize(so) for so in orders]), 200


@scheduled_order_bp.route("", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.scheduled_orders")
def create_scheduled_order():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    data = request.get_json(force=True) or {}

    restaurant_id = data.get("restaurant_id")
    items = data.get("items") or []
    address_text = (data.get("address") or "").strip()
    payment_method = data.get("payment_method")
    scheduled_for_raw = data.get("scheduled_for")

    if payment_method not in ("cod", "wallet"):
        return jsonify({"error": "Scheduled orders support Cash on Delivery or Wallet payment only."}), 400
    if not has_permission(customer.id, "customer", {"cod": "customer.cod", "wallet": "customer.wallet"}[payment_method]):
        return jsonify({"error": "This payment method has been restricted by the administrator."}), 403
    if not address_text:
        return jsonify({"error": "Delivery address is required."}), 400
    if not items or not isinstance(items, list):
        return jsonify({"error": "At least one food item is required."}), 400

    try:
        scheduled_for = datetime.fromisoformat(scheduled_for_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "scheduled_for must be a valid ISO 8601 datetime."}), 400

    # The browser sends a timezone-aware ISO string (e.g. with a +05:30 or Z
    # offset from a <input type="datetime-local"> converted client-side).
    # The rest of this module (and _convert_if_due) compares against
    # datetime.utcnow(), which is naive, so normalize to a naive UTC value
    # here once rather than special-casing every comparison downstream.
    if scheduled_for.tzinfo is not None:
        scheduled_for = scheduled_for.astimezone(timezone.utc).replace(tzinfo=None)

    if scheduled_for <= datetime.utcnow() + timedelta(minutes=10):
        return jsonify({"error": "Scheduled time must be at least 10 minutes in the future."}), 400

    restaurant = Restaurant.query.filter_by(id=restaurant_id, status="approved").first()
    if not restaurant:
        return jsonify({"error": "Restaurant not found or not currently accepting orders."}), 404

    resolved_items = []
    for it in items:
        food = Food.query.filter_by(id=it.get("food_id"), restaurant_id=restaurant.id).first()
        if not food or not food.is_available:
            return jsonify({"error": f"Food id {it.get('food_id')} is not available at this restaurant."}), 400
        qty = int(it.get("quantity", 1))
        if qty < 1:
            return jsonify({"error": "Item quantity must be at least 1."}), 400
        resolved_items.append((food.id, qty))

    so = ScheduledOrder(
        customer_id=customer.id, restaurant_id=restaurant.id, address_text=address_text,
        payment_method=payment_method, scheduled_for=scheduled_for, status="scheduled",
    )
    db.session.add(so)
    db.session.flush()
    for food_id, qty in resolved_items:
        db.session.add(ScheduledOrderItem(scheduled_order_id=so.id, food_id=food_id, quantity=qty))
    db.session.commit()

    return jsonify(_serialize(so)), 201


@scheduled_order_bp.route("/<int:scheduled_order_id>", methods=["DELETE"])
@token_required(["customer"])
@require_permission("customer.scheduled_orders")
def cancel_scheduled_order(scheduled_order_id):
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    so = ScheduledOrder.query.filter_by(id=scheduled_order_id, customer_id=customer.id).first()
    if not so:
        return jsonify({"error": "Scheduled order not found."}), 404
    if so.status != "scheduled":
        return jsonify({"error": f"This scheduled order can no longer be cancelled (status: '{so.status}')."}), 400
    if (so.scheduled_for - datetime.utcnow()) <= CANCELLATION_CUTOFF:
        return jsonify({"error": "Too close to the scheduled time to cancel."}), 400

    so.status = "cancelled"
    db.session.commit()
    return jsonify(_serialize(so)), 200