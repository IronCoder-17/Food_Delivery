"""
One-Tap Reorder ("Order Again"). Re-adds items from a past order to the
customer's cart -- but re-validates availability, stock, and *current*
price for every item; nothing is blindly copied from the old order.
"""
from flask import Blueprint, jsonify, g

from backend.models.models import db, Customer, Cart, CartItem, Food, Order
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission

reorder_bp = Blueprint("reorder", __name__, url_prefix="/api/customer/reorder")


@reorder_bp.route("/<int:order_id>", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.reorder")
def reorder(order_id):
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    order = Order.query.get(order_id)
    if not order or order.customer_id != customer.id:
        return jsonify({"error": "Order not found."}), 404

    cart = Cart.query.filter_by(customer_id=customer.id).first()
    existing_cart_item = CartItem.query.filter_by(cart_id=cart.id).first()
    if existing_cart_item:
        cart_restaurant_id = (existing_cart_item.food.restaurant_id if existing_cart_item.food_id
                              else existing_cart_item.combo.restaurant_id)
        if cart_restaurant_id != order.restaurant_id:
            return jsonify({
                "error": "Your cart already has items from a different restaurant. "
                         "Clear your cart first, then try Order Again."
            }), 409

    added, unavailable = [], []

    for item in order.items:
        # Combos aren't reconstructed automatically -- their line-up may have
        # changed entirely since the original order, so we surface it as
        # unavailable and let the customer re-add the (current) combo manually.
        if item.combo_id or not item.food_id:
            unavailable.append({"name": item.food_name, "reason": "This item is currently unavailable."})
            continue

        food = Food.query.get(item.food_id)
        if not food or not food.is_available:
            unavailable.append({"name": item.food_name, "reason": "This item is currently unavailable."})
            continue

        qty = item.quantity
        if food.track_inventory:
            available = food.stock_quantity or 0
            if available <= 0:
                unavailable.append({"name": food.name, "reason": "This item is currently unavailable."})
                continue
            qty = min(qty, available)

        existing = CartItem.query.filter_by(cart_id=cart.id, food_id=food.id).first()
        if existing:
            new_qty = existing.quantity + qty
            if food.track_inventory:
                new_qty = min(new_qty, food.stock_quantity or 0)
            existing.quantity = new_qty
        else:
            db.session.add(CartItem(cart_id=cart.id, food_id=food.id, quantity=qty))

        added.append({"food_id": food.id, "name": food.name, "quantity": qty, "current_price": food.final_price})

    db.session.commit()

    return jsonify({"added": added, "unavailable": unavailable}), 200
