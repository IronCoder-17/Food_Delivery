from flask import Blueprint, request, jsonify, g

from backend.models.models import Customer, Order, DisputeTicket
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.dispute_service import create_dispute, serialize_dispute, VALID_REASONS

dispute_bp = Blueprint("dispute", __name__, url_prefix="/api/customer/disputes")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


@dispute_bp.route("", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.disputes")
def open_dispute():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}

    order = Order.query.get(data.get("order_id"))
    if not order or order.customer_id != customer.id:
        return jsonify({"error": "Order not found."}), 404

    reason = data.get("reason")
    if reason not in VALID_REASONS:
        return jsonify({"error": f"Reason must be one of: {', '.join(sorted(VALID_REASONS))}."}), 400

    try:
        ticket = create_dispute(customer, order, reason, data.get("description"), data.get("evidence_url"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(serialize_dispute(ticket)), 201


@dispute_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.disputes")
def my_disputes():
    customer = _get_own_customer()
    tickets = DisputeTicket.query.filter_by(customer_id=customer.id).order_by(DisputeTicket.created_at.desc()).all()
    return jsonify([serialize_dispute(t) for t in tickets]), 200


@dispute_bp.route("/<int:dispute_id>", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.disputes")
def get_my_dispute(dispute_id):
    customer = _get_own_customer()
    ticket = DisputeTicket.query.filter_by(id=dispute_id, customer_id=customer.id).first()
    if not ticket:
        return jsonify({"error": "Dispute not found."}), 404
    return jsonify(serialize_dispute(ticket, include_events=True)), 200
