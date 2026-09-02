from flask import Blueprint, jsonify, g

from backend.models.models import Customer
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services import streak_service

streak_bp = Blueprint("streak", __name__, url_prefix="/api/customer/streak")


@streak_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.food_streaks")
def get_streak():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    streak = streak_service.get_or_create(customer.id)
    return jsonify(streak_service.serialize(streak)), 200
