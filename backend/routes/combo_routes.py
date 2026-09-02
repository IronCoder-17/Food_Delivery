"""
Combo / Bundle deals. Restaurant-managed; customers browse and add a whole
combo to cart in one action. combo_price is always what the restaurant set
it to -- the "original_price" (sum of constituent food prices) is computed
live from current Food prices for an honest "you save ₹X" display, never
stored/stale.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Restaurant, Food, Combo, ComboItem
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.pricing_service import effective_combo_price

combo_bp = Blueprint("combo", __name__, url_prefix="/api/restaurant/combos")
public_combo_bp = Blueprint("public_combo", __name__, url_prefix="/api/combos")


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


def _serialize_combo(c: Combo, for_customer=False):
    price, flash_sale = effective_combo_price(c)
    data = {
        "id": c.id,
        "restaurant_id": c.restaurant_id,
        "restaurant_name": c.restaurant.restaurant_name if c.restaurant else None,
        "name": c.name,
        "description": c.description,
        "combo_price": float(c.combo_price),
        "effective_price": price,
        "flash_sale": flash_sale,
        "original_price": c.original_price,
        "image_url": c.image_url,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "is_active": bool(c.is_active),
        "is_currently_active": c.is_currently_active(),
        "items": [
            {"food_id": i.food_id, "food_name": i.food.name if i.food else None, "quantity": i.quantity}
            for i in c.items
        ],
    }
    if for_customer:
        data.pop("is_active", None)
    return data


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Public: browse a restaurant's active combos
# ---------------------------------------------------------------------------
@public_combo_bp.route("", methods=["GET"])
def public_list_combos():
    restaurant_id = request.args.get("restaurant_id", type=int)
    q = Combo.query.filter_by(is_active=True)
    if restaurant_id:
        q = q.filter_by(restaurant_id=restaurant_id)
    else:
        # No restaurant specified: surface active combos across all approved
        # restaurants (used by the customer dashboard's "Combos & Deals" strip).
        q = q.join(Restaurant, Combo.restaurant_id == Restaurant.id).filter(Restaurant.status == "approved")
    combos = q.order_by(Combo.created_at.desc()).limit(100).all()
    live = [c for c in combos if c.is_currently_active()]
    return jsonify([_serialize_combo(c, for_customer=True) for c in live]), 200


# ---------------------------------------------------------------------------
# Restaurant: manage own combos
# ---------------------------------------------------------------------------
@combo_bp.route("", methods=["GET"])
@token_required(["restaurant"])
def list_own_combos():
    r = _get_own_restaurant()
    combos = Combo.query.filter_by(restaurant_id=r.id).order_by(Combo.created_at.desc()).all()
    return jsonify([_serialize_combo(c) for c in combos]), 200


@combo_bp.route("", methods=["POST"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_combos")
def create_combo():
    r = _get_own_restaurant()
    data = request.get_json(force=True) or {}

    name = (data.get("name") or "").strip()
    items = data.get("items") or []
    combo_price = data.get("combo_price")

    if not name:
        return jsonify({"error": "Combo name is required."}), 400
    if not items or not isinstance(items, list):
        return jsonify({"error": "At least one food item is required."}), 400
    try:
        combo_price = float(combo_price)
        if combo_price <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "combo_price must be a positive number."}), 400

    # validate every food belongs to this restaurant
    resolved_items = []
    for it in items:
        food = Food.query.filter_by(id=it.get("food_id"), restaurant_id=r.id).first()
        if not food:
            return jsonify({"error": f"Food id {it.get('food_id')} not found in your menu."}), 400
        qty = int(it.get("quantity", 1))
        if qty < 1:
            return jsonify({"error": "Item quantity must be at least 1."}), 400
        resolved_items.append((food.id, qty))

    combo = Combo(
        restaurant_id=r.id, name=name, description=data.get("description"),
        combo_price=combo_price, image_url=data.get("image_url"),
        start_date=_parse_dt(data.get("start_date")), end_date=_parse_dt(data.get("end_date")),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(combo)
    db.session.flush()
    for food_id, qty in resolved_items:
        db.session.add(ComboItem(combo_id=combo.id, food_id=food_id, quantity=qty))
    db.session.commit()
    return jsonify(_serialize_combo(combo)), 201


def _own_combo_or_404(combo_id, restaurant_id):
    return Combo.query.filter_by(id=combo_id, restaurant_id=restaurant_id).first()


@combo_bp.route("/<int:combo_id>", methods=["PUT"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_combos")
def update_combo(combo_id):
    r = _get_own_restaurant()
    combo = _own_combo_or_404(combo_id, r.id)
    if not combo:
        return jsonify({"error": "Combo not found."}), 404

    data = request.get_json(force=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Combo name cannot be empty."}), 400
        combo.name = name
    if "description" in data:
        combo.description = data.get("description")
    if "combo_price" in data:
        try:
            price = float(data["combo_price"])
            if price <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "combo_price must be a positive number."}), 400
        combo.combo_price = price
    if "image_url" in data:
        combo.image_url = data.get("image_url")
    if "start_date" in data:
        combo.start_date = _parse_dt(data.get("start_date"))
    if "end_date" in data:
        combo.end_date = _parse_dt(data.get("end_date"))
    if "is_active" in data:
        combo.is_active = bool(data["is_active"])

    if "items" in data:
        items = data.get("items") or []
        if not items:
            return jsonify({"error": "At least one food item is required."}), 400
        resolved_items = []
        for it in items:
            food = Food.query.filter_by(id=it.get("food_id"), restaurant_id=r.id).first()
            if not food:
                return jsonify({"error": f"Food id {it.get('food_id')} not found in your menu."}), 400
            qty = int(it.get("quantity", 1))
            if qty < 1:
                return jsonify({"error": "Item quantity must be at least 1."}), 400
            resolved_items.append((food.id, qty))
        ComboItem.query.filter_by(combo_id=combo.id).delete()
        for food_id, qty in resolved_items:
            db.session.add(ComboItem(combo_id=combo.id, food_id=food_id, quantity=qty))

    db.session.commit()
    return jsonify(_serialize_combo(combo)), 200


@combo_bp.route("/<int:combo_id>", methods=["DELETE"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_combos")
def delete_combo(combo_id):
    r = _get_own_restaurant()
    combo = _own_combo_or_404(combo_id, r.id)
    if not combo:
        return jsonify({"error": "Combo not found."}), 404
    db.session.delete(combo)
    db.session.commit()
    return jsonify({"message": "Combo deleted."}), 200
