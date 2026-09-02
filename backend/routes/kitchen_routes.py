"""
Live Kitchen Load. Restaurant sets their own status; customers see it
(embedded in food/restaurant listings, see food_routes.py) BEFORE checkout.
"""
from flask import Blueprint, request, jsonify, g

from backend.models.models import Restaurant
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services import kitchen_service

kitchen_bp = Blueprint("kitchen", __name__, url_prefix="/api/restaurant/kitchen-status")


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


@kitchen_bp.route("", methods=["GET"])
@token_required(["restaurant"])
def get_own_kitchen_status():
    r = _get_own_restaurant()
    return jsonify(kitchen_service.get_or_default(r.id)), 200


@kitchen_bp.route("", methods=["PUT"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_kitchen_status")
def update_own_kitchen_status():
    r = _get_own_restaurant()
    data = request.get_json(force=True) or {}
    try:
        row = kitchen_service.set_status(
            r.id, data.get("status"), data.get("extra_minutes", 0),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(kitchen_service.serialize(row)), 200
