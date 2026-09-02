"""
Self-service authority endpoints: lets the currently authenticated customer
or restaurant fetch their OWN effective permission map (used by the
frontend to hide/disable UI elements the admin has restricted). This is a
UX convenience only -- the real enforcement happens via
@require_permission on each protected backend route.
"""
from flask import Blueprint, jsonify, g
from backend.models.models import Customer, Restaurant
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import get_effective_authorities

customer_authority_bp = Blueprint("customer_authority", __name__, url_prefix="/api/customer")
restaurant_authority_bp = Blueprint("restaurant_authority", __name__, url_prefix="/api/restaurant")


@customer_authority_bp.route("/authorities", methods=["GET"])
@token_required(["customer"])
def my_customer_authorities():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    if not customer:
        return jsonify({"error": "Customer profile not found."}), 404
    return jsonify(get_effective_authorities(customer.id, "customer")), 200


@restaurant_authority_bp.route("/authorities", methods=["GET"])
@token_required(["restaurant"])
def my_restaurant_authorities():
    restaurant = Restaurant.query.filter_by(user_id=g.user_id).first()
    if not restaurant:
        return jsonify({"error": "Restaurant profile not found."}), 404
    return jsonify(get_effective_authorities(restaurant.id, "restaurant")), 200
