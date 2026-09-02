from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Customer, PassPlan, QuickBitePass
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.wallet_service import debit_wallet
from backend.services.pass_service import subscribe, serialize_pass, serialize_plan, get_active_pass

pass_bp = Blueprint("pass", __name__, url_prefix="/api/customer/pass")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


@pass_bp.route("/plans", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.quickbite_pass")
def list_plans():
    plans = PassPlan.query.filter_by(is_active=True).order_by(PassPlan.price.asc()).all()
    return jsonify([serialize_plan(p) for p in plans]), 200


@pass_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.quickbite_pass")
def my_pass():
    customer = _get_own_customer()
    active = get_active_pass(customer.id)
    return jsonify(serialize_pass(active) if active else None), 200


@pass_bp.route("/subscribe", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.quickbite_pass")
def subscribe_to_pass():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}
    plan = PassPlan.query.filter_by(id=data.get("plan_id"), is_active=True).first()
    if not plan:
        return jsonify({"error": "Plan not found."}), 404

    try:
        debit_wallet(customer.id, float(plan.price), f"QuickBite Pass subscription: {plan.name}", "pass", plan.id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    new_pass = subscribe(customer, plan)
    return jsonify(serialize_pass(new_pass)), 201


@pass_bp.route("/cancel", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.quickbite_pass")
def cancel_pass():
    customer = _get_own_customer()
    active = get_active_pass(customer.id)
    if not active:
        return jsonify({"error": "No active pass to cancel."}), 404
    active.status = "cancelled"
    db.session.commit()
    return jsonify(serialize_pass(active)), 200
