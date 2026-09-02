"""
Leftover / Surplus Food Deals: restaurant management, public customer feed,
and admin monitoring.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Restaurant, Food, SurplusDeal
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.surplus_service import serialize

surplus_bp = Blueprint("surplus", __name__, url_prefix="/api/restaurant/surplus-deals")
public_surplus_bp = Blueprint("public_surplus", __name__, url_prefix="/api/surplus-deals")
admin_surplus_bp = Blueprint("admin_surplus", __name__, url_prefix="/api/admin/surplus-deals")


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


def _parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- restaurant
@surplus_bp.route("", methods=["GET"])
@token_required(["restaurant"])
def list_own_surplus_deals():
    r = _get_own_restaurant()
    deals = SurplusDeal.query.filter_by(restaurant_id=r.id).order_by(SurplusDeal.created_at.desc()).all()
    return jsonify([serialize(d, include_restaurant=False) for d in deals]), 200


@surplus_bp.route("", methods=["POST"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_surplus_deals")
def create_surplus_deal():
    r = _get_own_restaurant()
    data = request.get_json(force=True) or {}

    food = Food.query.filter_by(id=data.get("food_id"), restaurant_id=r.id).first()
    if not food:
        return jsonify({"error": "Food not found in your menu."}), 400

    try:
        discount_price = float(data.get("discount_price"))
        if discount_price <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "discount_price must be a positive number."}), 400

    original_price = data.get("original_price")
    original_price = float(original_price) if original_price is not None else float(food.final_price)
    if discount_price >= original_price:
        return jsonify({"error": "discount_price should be less than original_price."}), 400

    try:
        quantity_total = int(data.get("quantity_total"))
        if quantity_total < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "quantity_total must be a positive integer."}), 400

    order_deadline = _parse_dt(data.get("order_deadline"))
    expiry_time = _parse_dt(data.get("expiry_time"))
    if not order_deadline or not expiry_time:
        return jsonify({"error": "Valid order_deadline and expiry_time (ISO 8601) are required."}), 400
    if order_deadline > expiry_time:
        return jsonify({"error": "order_deadline can't be after expiry_time."}), 400

    deal = SurplusDeal(
        restaurant_id=r.id, food_id=food.id, original_price=original_price, discount_price=discount_price,
        quantity_total=quantity_total, order_deadline=order_deadline, expiry_time=expiry_time,
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(deal)
    db.session.commit()
    return jsonify(serialize(deal, include_restaurant=False)), 201


@surplus_bp.route("/<int:deal_id>", methods=["PUT"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_surplus_deals")
def update_surplus_deal(deal_id):
    r = _get_own_restaurant()
    deal = SurplusDeal.query.filter_by(id=deal_id, restaurant_id=r.id).first()
    if not deal:
        return jsonify({"error": "Surplus deal not found."}), 404

    data = request.get_json(force=True) or {}
    if "discount_price" in data:
        try:
            price = float(data["discount_price"])
            if price <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "discount_price must be a positive number."}), 400
        deal.discount_price = price
    if "quantity_total" in data:
        try:
            qty = int(data["quantity_total"])
            if qty < deal.quantity_sold:
                return jsonify({"error": f"quantity_total can't be less than the {deal.quantity_sold} already sold."}), 400
        except (TypeError, ValueError):
            return jsonify({"error": "quantity_total must be a valid integer."}), 400
        deal.quantity_total = qty
    if "order_deadline" in data:
        dt = _parse_dt(data["order_deadline"])
        if not dt:
            return jsonify({"error": "Invalid order_deadline."}), 400
        deal.order_deadline = dt
    if "expiry_time" in data:
        dt = _parse_dt(data["expiry_time"])
        if not dt:
            return jsonify({"error": "Invalid expiry_time."}), 400
        deal.expiry_time = dt
    if deal.order_deadline > deal.expiry_time:
        return jsonify({"error": "order_deadline can't be after expiry_time."}), 400
    if "is_active" in data:
        deal.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(serialize(deal, include_restaurant=False)), 200


@surplus_bp.route("/<int:deal_id>", methods=["DELETE"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_surplus_deals")
def delete_surplus_deal(deal_id):
    r = _get_own_restaurant()
    deal = SurplusDeal.query.filter_by(id=deal_id, restaurant_id=r.id).first()
    if not deal:
        return jsonify({"error": "Surplus deal not found."}), 404
    db.session.delete(deal)
    db.session.commit()
    return jsonify({"message": "Surplus deal deleted."}), 200


# -------------------------------------------------------------------- public
@public_surplus_bp.route("", methods=["GET"])
def list_available_surplus_deals():
    now = datetime.utcnow()
    candidates = SurplusDeal.query.filter(
        SurplusDeal.is_active.is_(True),
        SurplusDeal.order_deadline >= now,
        SurplusDeal.expiry_time >= now,
    ).order_by(SurplusDeal.order_deadline.asc()).all()
    available = [d for d in candidates if d.is_currently_available()]
    return jsonify([serialize(d) for d in available]), 200


# --------------------------------------------------------------------- admin
@admin_surplus_bp.route("", methods=["GET"])
@token_required(["admin"])
def admin_list_surplus_deals():
    deals = SurplusDeal.query.order_by(SurplusDeal.created_at.desc()).limit(500).all()
    return jsonify([serialize(d) for d in deals]), 200
