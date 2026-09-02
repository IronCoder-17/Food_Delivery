from flask import Blueprint, request, jsonify, g, current_app
from backend.models.models import db, Cart, CartItem, Food, Combo, Customer
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.pricing_service import effective_food_price, effective_combo_price

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")


def _get_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


def _serialize_cart(cart: Cart):
    items = []
    subtotal = 0.0
    for ci in cart.items_rel:
        if ci.food_id:
            f = ci.food
            price, flash_sale = effective_food_price(f)
            line_total = round(price * ci.quantity, 2)
            subtotal += line_total
            items.append({
                "id": ci.id, "type": "food",
                "food_id": f.id, "food_name": f.name, "food_image": f.image_url,
                "restaurant": f.restaurant.restaurant_name if f.restaurant else None,
                "unit_price": price, "flash_sale": flash_sale,
                "quantity": ci.quantity, "line_total": line_total,
                "is_available": bool(f.is_available) and (not f.track_inventory or (f.stock_quantity or 0) >= ci.quantity),
            })
        elif ci.combo_id:
            c = ci.combo
            price, flash_sale = effective_combo_price(c)
            line_total = round(price * ci.quantity, 2)
            subtotal += line_total
            items.append({
                "id": ci.id, "type": "combo",
                "combo_id": c.id, "food_name": c.name, "food_image": c.image_url,
                "restaurant": c.restaurant.restaurant_name if c.restaurant else None,
                "unit_price": price, "flash_sale": flash_sale,
                "quantity": ci.quantity, "line_total": line_total,
                "is_available": c.is_currently_active(),
            })
    delivery_fee = current_app.config["DELIVERY_FEE"] if items else 0
    return {
        "items": items,
        "subtotal": round(subtotal, 2),
        "delivery_fee": delivery_fee,
        "total": round(subtotal + delivery_fee, 2),
    }


# attach a convenience relationship lookup without editing model file twice
from backend.models.models import CartItem as _CI  # noqa
Cart.items_rel = property(lambda self: CartItem.query.filter_by(cart_id=self.id).all())


def _cart_restaurant_id(cart):
    """The single restaurant this cart currently belongs to, or None if empty."""
    existing = CartItem.query.filter_by(cart_id=cart.id).first()
    if not existing:
        return None
    if existing.food_id:
        return existing.food.restaurant_id
    return existing.combo.restaurant_id


@cart_bp.route("", methods=["GET"])
@token_required(["customer"])
def get_cart():
    customer = _get_customer()
    cart = Cart.query.filter_by(customer_id=customer.id).first()
    return jsonify(_serialize_cart(cart)), 200


@cart_bp.route("/add", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.add_cart")
def add_to_cart():
    data = request.get_json(force=True) or {}
    food_id = data.get("food_id")
    quantity = int(data.get("quantity", 1))
    if quantity < 1:
        return jsonify({"error": "Quantity must be at least 1."}), 400

    food = Food.query.get(food_id)
    if not food or not food.is_available:
        return jsonify({"error": "This food item is unavailable."}), 400

    customer = _get_customer()
    cart = Cart.query.filter_by(customer_id=customer.id).first()

    existing = CartItem.query.filter_by(cart_id=cart.id, food_id=food_id).first()
    requested_total_qty = quantity + (existing.quantity if existing else 0)

    if food.track_inventory:
        available = food.stock_quantity or 0
        if requested_total_qty > available:
            return jsonify({
                "error": f"Only {available} of this item left in stock." if available > 0
                else "This item is sold out."
            }), 400

    if existing:
        existing.quantity = requested_total_qty
    else:
        cart_restaurant_id = _cart_restaurant_id(cart)
        if cart_restaurant_id is not None and cart_restaurant_id != food.restaurant_id:
            return jsonify({"error": "Your cart contains items from another restaurant. Clear cart to add from a new restaurant."}), 400
        db.session.add(CartItem(cart_id=cart.id, food_id=food_id, quantity=quantity))

    db.session.commit()
    return jsonify(_serialize_cart(cart)), 200


@cart_bp.route("/add-combo", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.add_cart")
def add_combo_to_cart():
    data = request.get_json(force=True) or {}
    combo_id = data.get("combo_id")
    quantity = int(data.get("quantity", 1))
    if quantity < 1:
        return jsonify({"error": "Quantity must be at least 1."}), 400

    combo = Combo.query.get(combo_id)
    if not combo or not combo.is_currently_active():
        return jsonify({"error": "This combo is not currently available."}), 400

    customer = _get_customer()
    cart = Cart.query.filter_by(customer_id=customer.id).first()

    existing = CartItem.query.filter_by(cart_id=cart.id, combo_id=combo_id).first()
    if existing:
        existing.quantity += quantity
    else:
        cart_restaurant_id = _cart_restaurant_id(cart)
        if cart_restaurant_id is not None and cart_restaurant_id != combo.restaurant_id:
            return jsonify({"error": "Your cart contains items from another restaurant. Clear cart to add from a new restaurant."}), 400
        db.session.add(CartItem(cart_id=cart.id, combo_id=combo_id, quantity=quantity))

    db.session.commit()
    return jsonify(_serialize_cart(cart)), 200


@cart_bp.route("/update", methods=["PUT"])
@token_required(["customer"])
def update_cart_item():
    data = request.get_json(force=True) or {}
    item_id = data.get("cart_item_id")
    quantity = int(data.get("quantity", 1))

    customer = _get_customer()
    cart = Cart.query.filter_by(customer_id=customer.id).first()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return jsonify({"error": "Cart item not found."}), 404

    if quantity < 1:
        db.session.delete(item)
    else:
        if item.food_id and item.food.track_inventory:
            available = item.food.stock_quantity or 0
            if quantity > available:
                return jsonify({"error": f"Only {available} left in stock."}), 400
        item.quantity = quantity
    db.session.commit()
    return jsonify(_serialize_cart(cart)), 200


@cart_bp.route("/remove/<int:item_id>", methods=["DELETE"])
@token_required(["customer"])
def remove_cart_item(item_id):
    customer = _get_customer()
    cart = Cart.query.filter_by(customer_id=customer.id).first()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify(_serialize_cart(cart)), 200


@cart_bp.route("/clear", methods=["DELETE"])
@token_required(["customer"])
def clear_cart():
    customer = _get_customer()
    cart = Cart.query.filter_by(customer_id=customer.id).first()
    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()
    return jsonify(_serialize_cart(cart)), 200
