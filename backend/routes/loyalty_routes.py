from flask import Blueprint, jsonify, g
from backend.models.models import Customer
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services import loyalty_service
from backend.models.models import LoyaltyTransaction

loyalty_bp = Blueprint("loyalty", __name__, url_prefix="/api/customer/loyalty")


@loyalty_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.loyalty")
def my_loyalty():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    if not customer:
        return jsonify({"error": "Customer profile not found."}), 404
    loyalty = loyalty_service.get_or_create_loyalty(customer.id)
    return jsonify(loyalty_service.serialize_loyalty_summary(loyalty)), 200


@loyalty_bp.route("/transactions", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.loyalty")
def my_loyalty_transactions():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    if not customer:
        return jsonify({"error": "Customer profile not found."}), 404
    txns = (
        LoyaltyTransaction.query.filter_by(customer_id=customer.id)
        .order_by(LoyaltyTransaction.created_at.desc()).limit(100).all()
    )
    return jsonify([loyalty_service.serialize_transaction(t) for t in txns]), 200


@loyalty_bp.route("/levels", methods=["GET"])
@token_required(["customer"])
def loyalty_levels_public():
    """Publicly viewable (to any authenticated customer) rank ladder, so the
    dashboard can show all six ranks and their benefits, not just the
    customer's current one."""
    levels = loyalty_service.get_levels_ordered()
    return jsonify([loyalty_service.serialize_level(l) for l in levels if l.is_active]), 200
