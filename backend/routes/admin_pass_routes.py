from flask import Blueprint, request, jsonify

from backend.models.models import db, PassPlan, PassPlanRestaurant, Restaurant
from backend.middleware.auth_middleware import token_required
from backend.services.pass_service import serialize_plan

admin_pass_bp = Blueprint("admin_pass", __name__, url_prefix="/api/admin/pass-plans")


@admin_pass_bp.route("", methods=["GET"])
@token_required(["admin"])
def list_pass_plans():
    plans = PassPlan.query.order_by(PassPlan.created_at.desc()).all()
    return jsonify([serialize_plan(p) for p in plans]), 200


@admin_pass_bp.route("", methods=["POST"])
@token_required(["admin"])
def create_pass_plan():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Plan name is required."}), 400
    try:
        price = float(data.get("price"))
        duration_days = int(data.get("duration_days"))
        max_free = int(data.get("max_free_deliveries_per_period", 4))
        min_order = float(data.get("min_order_amount", 0))
        if price <= 0 or duration_days <= 0 or max_free < 0 or min_order < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid numeric fields."}), 400

    plan = PassPlan(
        name=name, price=price, duration_days=duration_days, min_order_amount=min_order,
        max_free_deliveries_per_period=max_free, is_active=bool(data.get("is_active", True)),
    )
    db.session.add(plan)
    db.session.flush()

    for rid in data.get("eligible_restaurant_ids") or []:
        if Restaurant.query.get(rid):
            db.session.add(PassPlanRestaurant(plan_id=plan.id, restaurant_id=rid))

    db.session.commit()
    return jsonify(serialize_plan(plan)), 201


@admin_pass_bp.route("/<int:plan_id>", methods=["PUT"])
@token_required(["admin"])
def update_pass_plan(plan_id):
    plan = PassPlan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found."}), 404
    data = request.get_json(force=True) or {}

    if "name" in data:
        plan.name = data["name"].strip() or plan.name
    if "price" in data:
        plan.price = float(data["price"])
    if "duration_days" in data:
        plan.duration_days = int(data["duration_days"])
    if "min_order_amount" in data:
        plan.min_order_amount = float(data["min_order_amount"])
    if "max_free_deliveries_per_period" in data:
        plan.max_free_deliveries_per_period = int(data["max_free_deliveries_per_period"])
    if "is_active" in data:
        plan.is_active = bool(data["is_active"])
    if "eligible_restaurant_ids" in data:
        PassPlanRestaurant.query.filter_by(plan_id=plan.id).delete()
        for rid in data["eligible_restaurant_ids"] or []:
            if Restaurant.query.get(rid):
                db.session.add(PassPlanRestaurant(plan_id=plan.id, restaurant_id=rid))

    db.session.commit()
    return jsonify(serialize_plan(plan)), 200


@admin_pass_bp.route("/<int:plan_id>", methods=["DELETE"])
@token_required(["admin"])
def delete_pass_plan(plan_id):
    plan = PassPlan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found."}), 404
    db.session.delete(plan)
    db.session.commit()
    return jsonify({"message": "Plan deleted."}), 200
