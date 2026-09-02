"""
Group Ordering. A host creates a group order for one restaurant, shares an
invite code, other authenticated customers join and add their own items to
a shared cart, everyone sees the live shared total and their own
contribution, the host locks it, then the host checks out (paying for the
whole group).

Backend-enforced invariants:
  * Only members can view/add items to a group order.
  * A member can only remove items THEY added -- never another member's.
  * No changes are possible once locked/completed/cancelled, or once the
    deadline has passed (checked server-side on every relevant call, not
    just at creation).
  * Only the host can lock or checkout.
  * Prices/availability are always recomputed at checkout, never trusted
    from whatever was true when an item was added.
"""
import secrets
import string
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from backend.models.models import (
    db, Customer, Restaurant, Food, GroupOrder, GroupOrderMember, GroupOrderItem, GroupOrderSuggestion,
    Order, OrderItem, Payment, Notification, OrderTrackingEvent,
)
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission, has_permission
from backend.services.pricing_service import effective_food_price, register_deal_usage
from backend.services.wallet_service import debit_wallet
from backend.services import group_voting_service, group_bill_service

group_order_bp = Blueprint("group_order", __name__, url_prefix="/api/customer/group-orders")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


def _generate_invite_code():
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "QB-" + "".join(secrets.choice(alphabet) for _ in range(6))
        if not GroupOrder.query.filter_by(invite_code=code).first():
            return code
    raise RuntimeError("Could not generate a unique invite code.")


def _membership_or_none(group_order_id, customer_id):
    return GroupOrderMember.query.filter_by(group_order_id=group_order_id, customer_id=customer_id).first()


def _serialize(go: GroupOrder, viewer_customer_id):
    items_by_member = {}
    group_total = 0.0
    my_contribution = 0.0

    for item in go.items:
        food = item.food
        price, flash_sale = effective_food_price(food) if food else (0, None)
        line_total = round(price * item.quantity, 2)
        group_total += line_total
        if item.customer_id == viewer_customer_id:
            my_contribution += line_total

        entry = items_by_member.setdefault(item.customer_id, {
            "customer_id": item.customer_id,
            "customer_name": f"{item.customer.first_name} {item.customer.last_name[0]}." if item.customer else "Member",
            "items": [], "subtotal": 0.0,
        })
        entry["items"].append({
            "id": item.id, "food_id": item.food_id, "food_name": food.name if food else "Unavailable item",
            "unit_price": price, "quantity": item.quantity, "line_total": line_total,
            "is_available": bool(food and food.is_available),
            "can_remove": item.customer_id == viewer_customer_id,
        })
        entry["subtotal"] = round(entry["subtotal"] + line_total, 2)

    return {
        "id": go.id,
        "name": go.name,
        "invite_code": go.invite_code,
        "host_customer_id": go.host_customer_id,
        "is_host": go.host_customer_id == viewer_customer_id,
        "restaurant_id": go.restaurant_id,
        "restaurant_name": go.restaurant.restaurant_name if go.restaurant else None,
        "deadline": go.deadline.isoformat() if go.deadline else None,
        "status": go.status,
        "is_past_deadline": go.is_past_deadline(),
        "created_order_id": go.created_order_id,
        "group_total": round(group_total, 2),
        "my_contribution": round(my_contribution, 2),
        "enable_voting": bool(go.enable_voting),
        "voting_deadline": go.voting_deadline.isoformat() if go.voting_deadline else None,
        "max_participants": go.max_participants,
        "budget": float(go.budget) if go.budget is not None else None,
        "over_budget": bool(go.budget is not None and group_total > float(go.budget)),
        "bill_split_started": group_bill_service.has_been_split(go.id),
        "members": [{
            "customer_id": m.customer_id,
            "name": f"{m.customer.first_name} {m.customer.last_name[0]}." if m.customer else "Member",
            "is_host": m.customer_id == go.host_customer_id,
        } for m in go.members],
        "contributions": list(items_by_member.values()),
        "created_at": go.created_at.isoformat() if go.created_at else None,
    }


def _require_membership(go, customer):
    """Returns an error response tuple, or None if the caller is a member."""
    if not _membership_or_none(go.id, customer.id):
        return jsonify({"error": "You are not a member of this group order."}), 403
    return None


@group_order_bp.route("", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def create_group_order():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}

    name = (data.get("name") or "").strip()
    restaurant_id = data.get("restaurant_id")
    if not name:
        return jsonify({"error": "Group name is required."}), 400
    restaurant = Restaurant.query.filter_by(id=restaurant_id, status="approved").first()
    if not restaurant:
        return jsonify({"error": "Restaurant not found or not currently accepting orders."}), 404

    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.fromisoformat(data["deadline"])
        except ValueError:
            return jsonify({"error": "Invalid deadline format."}), 400
        if deadline <= datetime.utcnow():
            return jsonify({"error": "Deadline must be in the future."}), 400

    voting_deadline = None
    if data.get("voting_deadline"):
        try:
            voting_deadline = datetime.fromisoformat(data["voting_deadline"])
        except ValueError:
            return jsonify({"error": "Invalid voting_deadline format."}), 400

    max_participants = data.get("max_participants")
    if max_participants is not None:
        try:
            max_participants = int(max_participants)
            if max_participants < 1:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "max_participants must be a positive integer."}), 400

    budget = data.get("budget")
    if budget is not None:
        try:
            budget = float(budget)
            if budget <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "budget must be a positive number."}), 400

    go = GroupOrder(
        name=name, host_customer_id=customer.id, restaurant_id=restaurant.id,
        invite_code=_generate_invite_code(), deadline=deadline, status="open",
        enable_voting=bool(data.get("enable_voting", False)),
        voting_deadline=voting_deadline, max_participants=max_participants, budget=budget,
    )
    db.session.add(go)
    db.session.flush()
    db.session.add(GroupOrderMember(group_order_id=go.id, customer_id=customer.id))
    db.session.commit()

    return jsonify(_serialize(go, customer.id)), 201


@group_order_bp.route("/mine", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def list_my_group_orders():
    customer = _get_own_customer()
    memberships = GroupOrderMember.query.filter_by(customer_id=customer.id).all()
    group_orders = [m.group_order for m in memberships]
    group_orders.sort(key=lambda g: g.created_at, reverse=True)
    return jsonify([_serialize(go, customer.id) for go in group_orders]), 200


@group_order_bp.route("/join", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def join_group_order():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}
    code = (data.get("invite_code") or "").strip().upper()

    go = GroupOrder.query.filter_by(invite_code=code).first()
    if not go:
        return jsonify({"error": "Invalid invite code."}), 404
    if go.status != "open":
        return jsonify({"error": f"This group order is no longer open (status: {go.status})."}), 400
    if go.is_past_deadline():
        return jsonify({"error": "This group order's deadline has passed."}), 400

    already_member = _membership_or_none(go.id, customer.id)
    if not already_member and go.max_participants and len(go.members) >= go.max_participants:
        return jsonify({"error": f"This group order is full ({go.max_participants} participants max)."}), 400

    if not already_member:
        db.session.add(GroupOrderMember(group_order_id=go.id, customer_id=customer.id))
        db.session.commit()

    return jsonify(_serialize(go, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def get_group_order(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    return jsonify(_serialize(go, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>/items", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def add_group_item(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    if go.status != "open" or go.is_past_deadline():
        return jsonify({"error": "This group order is no longer accepting new items."}), 400

    data = request.get_json(force=True) or {}
    food = Food.query.filter_by(id=data.get("food_id"), restaurant_id=go.restaurant_id).first()
    if not food or not food.is_available:
        return jsonify({"error": "This food item is unavailable at this restaurant."}), 400
    quantity = int(data.get("quantity", 1))
    if quantity < 1:
        return jsonify({"error": "Quantity must be at least 1."}), 400
    if food.track_inventory and quantity > (food.stock_quantity or 0):
        return jsonify({"error": f"Only {food.stock_quantity or 0} left in stock."}), 400

    db.session.add(GroupOrderItem(group_order_id=go.id, customer_id=customer.id, food_id=food.id, quantity=quantity))
    db.session.commit()
    return jsonify(_serialize(go, customer.id)), 201


@group_order_bp.route("/<int:group_order_id>/items/<int:item_id>", methods=["DELETE"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def remove_group_item(group_order_id, item_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    if go.status != "open":
        return jsonify({"error": "This group order is locked; items can no longer be changed."}), 400

    item = GroupOrderItem.query.filter_by(id=item_id, group_order_id=go.id).first()
    if not item:
        return jsonify({"error": "Item not found."}), 404
    if item.customer_id != customer.id:
        return jsonify({"error": "You can only remove items you added yourself."}), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify(_serialize(go, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>/lock", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def lock_group_order(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    if go.host_customer_id != customer.id:
        return jsonify({"error": "Only the host can lock this group order."}), 403
    if go.status != "open":
        return jsonify({"error": f"Group order is already '{go.status}'."}), 400
    if not go.items:
        return jsonify({"error": "Cannot lock an empty group order."}), 400

    go.status = "locked"
    db.session.commit()
    return jsonify(_serialize(go, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>/checkout", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def checkout_group_order(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    if go.host_customer_id != customer.id:
        return jsonify({"error": "Only the host can check out this group order."}), 403
    if go.status not in ("open", "locked"):
        return jsonify({"error": f"Group order cannot be checked out (status: {go.status})."}), 400
    if not go.items:
        return jsonify({"error": "Cannot check out an empty group order."}), 400

    data = request.get_json(force=True) or {}
    payment_method = data.get("payment_method")
    address_text = (data.get("address") or "").strip()
    if payment_method not in ("cod", "wallet"):
        return jsonify({"error": "Group checkout supports Cash on Delivery or Wallet payment only."}), 400
    if not has_permission(customer.id, "customer", {"cod": "customer.cod", "wallet": "customer.wallet"}[payment_method]):
        return jsonify({"error": "This payment method has been restricted by the administrator."}), 403
    if not address_text:
        return jsonify({"error": "Delivery address is required."}), 400

    subtotal = 0.0
    line_specs = []
    for item in go.items:
        food = Food.query.get(item.food_id)
        if not food or not food.is_available or food.restaurant_id != go.restaurant_id:
            return jsonify({"error": f"'{item.food.name if item.food else 'An item'}' is no longer available."}), 400
        if food.track_inventory and (food.stock_quantity or 0) < item.quantity:
            return jsonify({"error": f"'{food.name}' no longer has enough stock."}), 400
        price, flash_sale = effective_food_price(food)
        line_total = round(price * item.quantity, 2)
        subtotal += line_total
        line_specs.append({
            "food": food, "quantity": item.quantity, "unit_price": price, "line_total": line_total,
            "deal_info": flash_sale,
        })

    delivery_fee = 40.0
    total = round(subtotal + delivery_fee, 2)

    order = Order(
        customer_id=go.host_customer_id, restaurant_id=go.restaurant_id, address_text=address_text,
        subtotal=round(subtotal, 2), discount_amount=0, delivery_fee=delivery_fee, total_amount=total,
        payment_method=payment_method, payment_status="pending", order_status="placed",
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderTrackingEvent(order_id=order.id, status="placed", note=f"Placed from group order '{go.name}'."))

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
        if spec["deal_info"]:
            register_deal_usage(spec["deal_info"], spec["quantity"])

    if payment_method == "wallet":
        try:
            debit_wallet(go.host_customer_id, total, f"Group order #{order.id} payment", "order", order.id)
            order.payment_status = "paid"
            db.session.add(Payment(order_id=order.id, method="wallet", amount=total, status="success"))
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
    else:
        db.session.add(Payment(order_id=order.id, method="cod", amount=total, status="pending"))

    go.status = "completed"
    go.created_order_id = order.id

    for member in go.members:
        db.session.add(Notification(
            recipient_role="customer", recipient_id=member.customer_id,
            title="Group Order Placed", message=f"'{go.name}' has been placed as Order #{order.id}.",
        ))

    db.session.commit()
    return jsonify(_serialize(go, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>/cancel", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.group_ordering")
def cancel_group_order(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    if go.host_customer_id != customer.id:
        return jsonify({"error": "Only the host can cancel this group order."}), 403
    if go.status not in ("open", "locked"):
        return jsonify({"error": f"Group order cannot be cancelled (status: {go.status})."}), 400

    go.status = "cancelled"
    db.session.commit()
    return jsonify(_serialize(go, customer.id)), 200


# ------------------------------------------------------------------
# Live Group Order Voting (additive -- only relevant when the host has
# enable_voting=True; the direct-add endpoints above still work regardless)
# ------------------------------------------------------------------
@group_order_bp.route("/<int:group_order_id>/suggestions", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.group_voting")
def list_suggestions(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    return jsonify(group_voting_service.list_suggestions(go.id, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>/suggestions", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_voting")
def suggest_dish(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    if not go.enable_voting:
        return jsonify({"error": "Voting is not enabled for this group order."}), 400
    if go.status != "open":
        return jsonify({"error": "This group order is no longer open."}), 400

    data = request.get_json(force=True) or {}
    try:
        suggestion = group_voting_service.add_suggestion(go, customer.id, data.get("food_id"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(group_voting_service.serialize_suggestion(suggestion, customer.id)), 201


@group_order_bp.route("/<int:group_order_id>/suggestions/<int:suggestion_id>/vote", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_voting")
def vote_for_suggestion(group_order_id, suggestion_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    if go.voting_deadline and datetime.utcnow() > go.voting_deadline:
        return jsonify({"error": "Voting has closed for this group order."}), 400

    suggestion = GroupOrderSuggestion.query.filter_by(id=suggestion_id, group_order_id=go.id).first()
    if not suggestion:
        return jsonify({"error": "Suggestion not found."}), 404

    group_voting_service.cast_vote(suggestion, customer.id)
    return jsonify(group_voting_service.serialize_suggestion(suggestion, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>/suggestions/<int:suggestion_id>/vote", methods=["DELETE"])
@token_required(["customer"])
@require_permission("customer.group_voting")
def unvote_suggestion(group_order_id, suggestion_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err

    suggestion = GroupOrderSuggestion.query.filter_by(id=suggestion_id, group_order_id=go.id).first()
    if not suggestion:
        return jsonify({"error": "Suggestion not found."}), 404

    group_voting_service.remove_vote(suggestion, customer.id)
    return jsonify(group_voting_service.serialize_suggestion(suggestion, customer.id)), 200


@group_order_bp.route("/<int:group_order_id>/finalize-voting", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_voting")
def finalize_voting(group_order_id):
    """Host-only: converts the current voting leader(s) into real shared-cart
    items. Safe to call more than once (idempotent per food item)."""
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    if go.host_customer_id != customer.id:
        return jsonify({"error": "Only the host can finalize voting."}), 403
    if go.status != "open":
        return jsonify({"error": "This group order is no longer open."}), 400

    added_food_ids = group_voting_service.finalize_voting(go)
    db.session.refresh(go)
    return jsonify({"added_food_ids": added_food_ids, "group_order": _serialize(go, customer.id)}), 200


# ------------------------------------------------------------------
# Group Bill Splitting (real wallet-based reimbursement -- see
# backend/services/group_bill_service.py for the full design rationale)
# ------------------------------------------------------------------
@group_order_bp.route("/<int:group_order_id>/split-bill", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_bill_split")
def split_bill(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    if go.host_customer_id != customer.id:
        return jsonify({"error": "Only the host can split the bill."}), 403
    if go.status != "completed":
        return jsonify({"error": "The group order must be checked out before splitting the bill."}), 400

    data = request.get_json(force=True) or {}
    try:
        rows = group_bill_service.split_bill(go, data.get("split_type", "equal"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify([group_bill_service.serialize(r) for r in rows]), 201


@group_order_bp.route("/<int:group_order_id>/bill-split", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.group_bill_split")
def get_bill_split(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    from backend.models.models import GroupOrderPayment
    rows = GroupOrderPayment.query.filter_by(group_order_id=go.id).all()
    return jsonify([group_bill_service.serialize(r) for r in rows]), 200


@group_order_bp.route("/<int:group_order_id>/pay-share", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_bill_split")
def pay_my_share(group_order_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    err = _require_membership(go, customer)
    if err:
        return err
    try:
        row = group_bill_service.pay_my_share(go, customer.id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(group_bill_service.serialize(row)), 200


@group_order_bp.route("/<int:group_order_id>/refund-share/<int:target_customer_id>", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.group_bill_split")
def refund_member_share(group_order_id, target_customer_id):
    customer = _get_own_customer()
    go = GroupOrder.query.get(group_order_id)
    if not go:
        return jsonify({"error": "Group order not found."}), 404
    if go.host_customer_id != customer.id:
        return jsonify({"error": "Only the host can issue a refund."}), 403
    try:
        row = group_bill_service.refund_share(go, target_customer_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(group_bill_service.serialize(row)), 200
