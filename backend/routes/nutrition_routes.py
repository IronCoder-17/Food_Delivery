from flask import Blueprint, request, jsonify, g

from backend.models.models import Customer, Order
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services import nutrition_service

nutrition_bp = Blueprint("nutrition", __name__, url_prefix="/api/customer/nutrition")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


@nutrition_bp.route("/preview/<int:order_id>", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.nutrition_tracking")
def preview_order_nutrition(order_id):
    customer = _get_own_customer()
    order = Order.query.filter_by(id=order_id, customer_id=customer.id).first()
    if not order:
        return jsonify({"error": "Order not found."}), 404
    return jsonify(nutrition_service.order_nutrition_preview(order)), 200


@nutrition_bp.route("/log", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.nutrition_tracking")
def log_order():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}
    try:
        log = nutrition_service.log_order(customer.id, data.get("order_id"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(nutrition_service.serialize_log(log)), 201


@nutrition_bp.route("/summary", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.nutrition_tracking")
def get_summary():
    customer = _get_own_customer()
    range_type = request.args.get("range", "daily")
    if range_type == "weekly":
        return jsonify(nutrition_service.weekly_summary(customer.id)), 200
    return jsonify(nutrition_service.daily_summary(customer.id)), 200


@nutrition_bp.route("/export", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.nutrition_tracking")
def export_data():
    customer = _get_own_customer()
    return jsonify(nutrition_service.export_logs(customer.id)), 200
