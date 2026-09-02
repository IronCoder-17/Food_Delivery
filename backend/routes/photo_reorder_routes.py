from flask import Blueprint, request, jsonify, g

from backend.models.models import Customer
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services import photo_reorder_service

photo_reorder_bp = Blueprint("photo_reorder", __name__, url_prefix="/api/customer/photo-reorder")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


@photo_reorder_bp.route("/photo", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.photo_reorder")
def match_from_photo():
    customer = _get_own_customer()
    if not customer:
        return jsonify({"error": "Customer profile not found."}), 404

    file = request.files.get("image")
    try:
        image_bytes, mime_type = photo_reorder_service.validate_image(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    nearby_only = request.form.get("nearby_only", "true").lower() != "false"

    try:
        result = photo_reorder_service.match_photo_to_menu(customer, image_bytes, mime_type, nearby_only)
    except ValueError as e:
        return jsonify({"error": str(e), "needs_manual_input": True}), 200

    result["needs_manual_input"] = False
    return jsonify(result), 200


@photo_reorder_bp.route("/manual", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.photo_reorder")
def match_from_dish_name():
    customer = _get_own_customer()
    if not customer:
        return jsonify({"error": "Customer profile not found."}), 404

    data = request.get_json(force=True) or {}
    dish_name = (data.get("dish_name") or "").strip()
    if not dish_name:
        return jsonify({"error": "dish_name is required."}), 400

    nearby_only = bool(data.get("nearby_only", True))
    result = photo_reorder_service.match_dish_name_to_menu(dish_name, nearby_only, customer)
    result["needs_manual_input"] = False
    return jsonify(result), 200
