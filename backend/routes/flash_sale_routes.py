"""
Restaurant Flash Sales. Backend enforces timing and quantity caps -- a sale
is only ever "live" per FlashSale.is_currently_live(), and the discount
applied at checkout always comes from pricing_service, never the frontend.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Restaurant, Food, Combo, FlashSale
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission

flash_sale_bp = Blueprint("flash_sale", __name__, url_prefix="/api/restaurant/flash-sales")


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


def _serialize(s: FlashSale):
    return {
        "id": s.id,
        "food_id": s.food_id,
        "food_name": s.food.name if s.food else None,
        "combo_id": s.combo_id,
        "combo_name": s.combo.name if s.combo else None,
        "discount_percent": float(s.discount_percent),
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat(),
        "max_quantity": s.max_quantity,
        "sold_quantity": s.sold_quantity,
        "is_active": bool(s.is_active),
        "is_currently_live": s.is_currently_live(),
    }


def _parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@flash_sale_bp.route("", methods=["GET"])
@token_required(["restaurant"])
def list_flash_sales():
    r = _get_own_restaurant()
    sales = FlashSale.query.filter_by(restaurant_id=r.id).order_by(FlashSale.created_at.desc()).all()
    return jsonify([_serialize(s) for s in sales]), 200


@flash_sale_bp.route("", methods=["POST"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_flash_sales")
def create_flash_sale():
    r = _get_own_restaurant()
    data = request.get_json(force=True) or {}

    food_id = data.get("food_id")
    combo_id = data.get("combo_id")
    if bool(food_id) == bool(combo_id):
        return jsonify({"error": "Provide exactly one of food_id or combo_id."}), 400

    if food_id and not Food.query.filter_by(id=food_id, restaurant_id=r.id).first():
        return jsonify({"error": "Food not found in your menu."}), 400
    if combo_id and not Combo.query.filter_by(id=combo_id, restaurant_id=r.id).first():
        return jsonify({"error": "Combo not found."}), 400

    try:
        discount = float(data.get("discount_percent"))
        if not (0 < discount <= 90):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "discount_percent must be between 0 and 90."}), 400

    start_time = _parse_dt(data.get("start_time"))
    end_time = _parse_dt(data.get("end_time"))
    if not start_time or not end_time:
        return jsonify({"error": "Valid start_time and end_time (ISO 8601) are required."}), 400
    if end_time <= start_time:
        return jsonify({"error": "end_time must be after start_time."}), 400

    max_quantity = data.get("max_quantity")
    if max_quantity is not None:
        try:
            max_quantity = int(max_quantity)
            if max_quantity < 1:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "max_quantity must be a positive integer, or omitted for unlimited."}), 400

    sale = FlashSale(
        restaurant_id=r.id, food_id=food_id, combo_id=combo_id,
        discount_percent=discount, start_time=start_time, end_time=end_time,
        max_quantity=max_quantity, is_active=bool(data.get("is_active", True)),
    )
    db.session.add(sale)
    db.session.commit()
    return jsonify(_serialize(sale)), 201


@flash_sale_bp.route("/<int:sale_id>", methods=["PUT"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_flash_sales")
def update_flash_sale(sale_id):
    r = _get_own_restaurant()
    sale = FlashSale.query.filter_by(id=sale_id, restaurant_id=r.id).first()
    if not sale:
        return jsonify({"error": "Flash sale not found."}), 404

    data = request.get_json(force=True) or {}
    if "discount_percent" in data:
        try:
            discount = float(data["discount_percent"])
            if not (0 < discount <= 90):
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "discount_percent must be between 0 and 90."}), 400
        sale.discount_percent = discount
    if "start_time" in data:
        dt = _parse_dt(data["start_time"])
        if not dt:
            return jsonify({"error": "Invalid start_time."}), 400
        sale.start_time = dt
    if "end_time" in data:
        dt = _parse_dt(data["end_time"])
        if not dt:
            return jsonify({"error": "Invalid end_time."}), 400
        sale.end_time = dt
    if sale.end_time <= sale.start_time:
        return jsonify({"error": "end_time must be after start_time."}), 400
    if "max_quantity" in data:
        sale.max_quantity = int(data["max_quantity"]) if data["max_quantity"] is not None else None
    if "is_active" in data:
        sale.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(_serialize(sale)), 200


@flash_sale_bp.route("/<int:sale_id>", methods=["DELETE"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_flash_sales")
def delete_flash_sale(sale_id):
    r = _get_own_restaurant()
    sale = FlashSale.query.filter_by(id=sale_id, restaurant_id=r.id).first()
    if not sale:
        return jsonify({"error": "Flash sale not found."}), 404
    db.session.delete(sale)
    db.session.commit()
    return jsonify({"message": "Flash sale deleted."}), 200
