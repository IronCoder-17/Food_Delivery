"""
Chef's Specials: restaurant management, public customer-facing feed
(currently-live only), and admin monitoring/removal.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Restaurant, Food, ChefSpecial
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.chef_special_service import serialize

chef_special_bp = Blueprint("chef_special", __name__, url_prefix="/api/restaurant/chef-specials")
public_chef_special_bp = Blueprint("public_chef_special", __name__, url_prefix="/api/chef-specials")
admin_chef_special_bp = Blueprint("admin_chef_special", __name__, url_prefix="/api/admin/chef-specials")


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


def _parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- restaurant
@chef_special_bp.route("", methods=["GET"])
@token_required(["restaurant"])
def list_own_chef_specials():
    r = _get_own_restaurant()
    specials = ChefSpecial.query.filter_by(restaurant_id=r.id).order_by(ChefSpecial.created_at.desc()).all()
    return jsonify([serialize(s, include_restaurant=False) for s in specials]), 200


@chef_special_bp.route("", methods=["POST"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_chefs_specials")
def create_chef_special():
    r = _get_own_restaurant()
    data = request.get_json(force=True) or {}

    food_id = data.get("food_id")
    food = Food.query.filter_by(id=food_id, restaurant_id=r.id).first() if food_id else None
    if not food:
        return jsonify({"error": "Food not found in your menu."}), 400

    try:
        special_price = float(data.get("special_price"))
        if special_price <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "special_price must be a positive number."}), 400
    if special_price >= float(food.final_price):
        return jsonify({"error": "special_price should be less than the food's current price."}), 400

    try:
        quantity_total = int(data.get("quantity_total"))
        if quantity_total < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "quantity_total must be a positive integer."}), 400

    start_time = _parse_dt(data.get("start_time"))
    end_time = _parse_dt(data.get("end_time"))
    if not start_time or not end_time:
        return jsonify({"error": "Valid start_time and end_time (ISO 8601) are required."}), 400
    if end_time <= start_time:
        return jsonify({"error": "end_time must be after start_time."}), 400

    special = ChefSpecial(
        restaurant_id=r.id, food_id=food.id, special_price=special_price,
        quantity_total=quantity_total, start_time=start_time, end_time=end_time,
        description=(data.get("description") or "").strip() or None,
        image_url=(data.get("image_url") or "").strip() or None,
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(special)
    db.session.commit()
    return jsonify(serialize(special, include_restaurant=False)), 201


@chef_special_bp.route("/<int:special_id>", methods=["PUT"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_chefs_specials")
def update_chef_special(special_id):
    r = _get_own_restaurant()
    special = ChefSpecial.query.filter_by(id=special_id, restaurant_id=r.id).first()
    if not special:
        return jsonify({"error": "Chef's Special not found."}), 404

    data = request.get_json(force=True) or {}
    if "special_price" in data:
        try:
            price = float(data["special_price"])
            if price <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "special_price must be a positive number."}), 400
        special.special_price = price
    if "quantity_total" in data:
        try:
            qty = int(data["quantity_total"])
            if qty < special.quantity_sold:
                return jsonify({"error": f"quantity_total can't be less than the {special.quantity_sold} already sold."}), 400
        except (TypeError, ValueError):
            return jsonify({"error": "quantity_total must be a valid integer."}), 400
        special.quantity_total = qty
    if "start_time" in data:
        dt = _parse_dt(data["start_time"])
        if not dt:
            return jsonify({"error": "Invalid start_time."}), 400
        special.start_time = dt
    if "end_time" in data:
        dt = _parse_dt(data["end_time"])
        if not dt:
            return jsonify({"error": "Invalid end_time."}), 400
        special.end_time = dt
    if special.end_time <= special.start_time:
        return jsonify({"error": "end_time must be after start_time."}), 400
    if "description" in data:
        special.description = (data.get("description") or "").strip() or None
    if "image_url" in data:
        special.image_url = (data.get("image_url") or "").strip() or None
    if "is_active" in data:
        special.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(serialize(special, include_restaurant=False)), 200


@chef_special_bp.route("/<int:special_id>", methods=["DELETE"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_chefs_specials")
def delete_chef_special(special_id):
    r = _get_own_restaurant()
    special = ChefSpecial.query.filter_by(id=special_id, restaurant_id=r.id).first()
    if not special:
        return jsonify({"error": "Chef's Special not found."}), 404
    db.session.delete(special)
    db.session.commit()
    return jsonify({"message": "Chef's Special deleted."}), 200


# -------------------------------------------------------------------- public
@public_chef_special_bp.route("", methods=["GET"])
def list_live_chef_specials():
    now = datetime.utcnow()
    candidates = ChefSpecial.query.filter(
        ChefSpecial.is_active.is_(True),
        ChefSpecial.start_time <= now,
        ChefSpecial.end_time >= now,
    ).order_by(ChefSpecial.end_time.asc()).all()
    live = [s for s in candidates if s.is_currently_live()]
    return jsonify([serialize(s) for s in live]), 200


# --------------------------------------------------------------------- admin
@admin_chef_special_bp.route("", methods=["GET"])
@token_required(["admin"])
def admin_list_chef_specials():
    specials = ChefSpecial.query.order_by(ChefSpecial.created_at.desc()).limit(500).all()
    return jsonify([serialize(s) for s in specials]), 200


@admin_chef_special_bp.route("/<int:special_id>", methods=["DELETE"])
@token_required(["admin"])
def admin_delete_chef_special(special_id):
    """Admin can remove an inappropriate Chef's Special."""
    special = ChefSpecial.query.get(special_id)
    if not special:
        return jsonify({"error": "Chef's Special not found."}), 404
    db.session.delete(special)
    db.session.commit()
    return jsonify({"message": "Chef's Special removed by admin."}), 200
