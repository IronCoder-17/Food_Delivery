from flask import Blueprint, request, jsonify, g

from backend.models.models import db, SubscriptionPlan, RestaurantSubscription, Admin
from backend.middleware.auth_middleware import token_required
from backend.services.subscription_service import (
    activate, cancel, sync_expiry, serialize_subscription, serialize_plan,
)

admin_subscription_bp = Blueprint("admin_subscription", __name__, url_prefix="/api/admin/subscriptions")


def _get_own_admin():
    return Admin.query.filter_by(user_id=g.user_id).first()


# ---------------------------------------------------------------------------
# Plan management
# ---------------------------------------------------------------------------
@admin_subscription_bp.route("/plans", methods=["GET"])
@token_required(["admin"])
def list_plans():
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.created_at.desc()).all()
    return jsonify([serialize_plan(p) for p in plans]), 200


@admin_subscription_bp.route("/plans", methods=["POST"])
@token_required(["admin"])
def create_plan():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Plan name is required."}), 400
    try:
        price = float(data.get("price"))
        duration_days = int(data.get("duration_days"))
        if price <= 0 or duration_days <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "price and duration_days must be positive numbers."}), 400

    granted = data.get("granted_permissions") or []
    plan = SubscriptionPlan(
        name=name, price=price, duration_days=duration_days, description=data.get("description"),
        granted_permissions=",".join(granted), is_active=bool(data.get("is_active", True)),
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify(serialize_plan(plan)), 201


@admin_subscription_bp.route("/plans/<int:plan_id>", methods=["PUT"])
@token_required(["admin"])
def update_plan(plan_id):
    plan = SubscriptionPlan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found."}), 404
    data = request.get_json(force=True) or {}
    if "name" in data:
        plan.name = data["name"].strip() or plan.name
    if "price" in data:
        plan.price = float(data["price"])
    if "duration_days" in data:
        plan.duration_days = int(data["duration_days"])
    if "description" in data:
        plan.description = data["description"]
    if "granted_permissions" in data:
        plan.granted_permissions = ",".join(data["granted_permissions"] or [])
    if "is_active" in data:
        plan.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify(serialize_plan(plan)), 200


# ---------------------------------------------------------------------------
# Restaurant subscription approvals
# ---------------------------------------------------------------------------
@admin_subscription_bp.route("", methods=["GET"])
@token_required(["admin"])
def list_subscriptions():
    status = request.args.get("status")
    q = RestaurantSubscription.query
    if status:
        q = q.filter_by(status=status)
    subs = q.order_by(RestaurantSubscription.requested_at.desc()).all()
    for s in subs:
        if s.status == "active":
            sync_expiry(s)
    return jsonify([serialize_subscription(s) for s in subs]), 200


@admin_subscription_bp.route("/<int:sub_id>/activate", methods=["PUT"])
@token_required(["admin"])
def activate_subscription(sub_id):
    admin = _get_own_admin()
    sub = RestaurantSubscription.query.get(sub_id)
    if not sub:
        return jsonify({"error": "Subscription not found."}), 404
    if sub.status not in ("pending", "expired", "cancelled"):
        return jsonify({"error": f"Subscription is already '{sub.status}'."}), 400
    activate(sub, admin.id)
    return jsonify(serialize_subscription(sub)), 200


@admin_subscription_bp.route("/<int:sub_id>/cancel", methods=["PUT"])
@token_required(["admin"])
def cancel_subscription(sub_id):
    admin = _get_own_admin()
    sub = RestaurantSubscription.query.get(sub_id)
    if not sub:
        return jsonify({"error": "Subscription not found."}), 404
    if sub.status != "active":
        return jsonify({"error": f"Subscription is not active (status: '{sub.status}')."}), 400
    cancel(sub, admin.id)
    return jsonify(serialize_subscription(sub)), 200
