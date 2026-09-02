from flask import Blueprint, request, jsonify, g

from backend.models.models import Restaurant, SubscriptionPlan, RestaurantSubscription
from backend.middleware.auth_middleware import token_required
from backend.services.subscription_service import request_plan, sync_expiry, serialize_subscription, serialize_plan

subscription_bp = Blueprint("subscription", __name__, url_prefix="/api/restaurant/subscription")


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


@subscription_bp.route("/plans", methods=["GET"])
@token_required(["restaurant"])
def list_available_plans():
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price.asc()).all()
    return jsonify([serialize_plan(p) for p in plans]), 200


@subscription_bp.route("", methods=["GET"])
@token_required(["restaurant"])
def my_subscription():
    r = _get_own_restaurant()
    sub = RestaurantSubscription.query.filter(
        RestaurantSubscription.restaurant_id == r.id,
        RestaurantSubscription.status.in_(["active", "pending"]),
    ).order_by(RestaurantSubscription.requested_at.desc()).first()
    if sub and sub.status == "active":
        sync_expiry(sub)
    return jsonify(serialize_subscription(sub) if sub else None), 200


@subscription_bp.route("/request", methods=["POST"])
@token_required(["restaurant"])
def request_subscription():
    r = _get_own_restaurant()
    data = request.get_json(force=True) or {}
    plan = SubscriptionPlan.query.filter_by(id=data.get("plan_id"), is_active=True).first()
    if not plan:
        return jsonify({"error": "Plan not found."}), 404

    existing_pending = RestaurantSubscription.query.filter_by(restaurant_id=r.id, status="pending").first()
    if existing_pending:
        return jsonify({"error": "You already have a pending subscription request awaiting admin approval."}), 400

    sub = request_plan(r.id, plan)
    return jsonify(serialize_subscription(sub)), 201
