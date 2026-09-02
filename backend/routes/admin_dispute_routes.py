from flask import Blueprint, request, jsonify, g

from backend.models.models import DisputeTicket, Admin
from backend.middleware.auth_middleware import token_required
from backend.services.dispute_service import update_status, resolve_with_refund, serialize_dispute

admin_dispute_bp = Blueprint("admin_dispute", __name__, url_prefix="/api/admin/disputes")


def _get_own_admin():
    return Admin.query.filter_by(user_id=g.user_id).first()


@admin_dispute_bp.route("", methods=["GET"])
@token_required(["admin"])
def list_disputes():
    status = request.args.get("status")
    q = DisputeTicket.query
    if status:
        q = q.filter_by(status=status)
    tickets = q.order_by(DisputeTicket.created_at.desc()).all()
    return jsonify([serialize_dispute(t) for t in tickets]), 200


@admin_dispute_bp.route("/<int:dispute_id>", methods=["GET"])
@token_required(["admin"])
def get_dispute(dispute_id):
    ticket = DisputeTicket.query.get(dispute_id)
    if not ticket:
        return jsonify({"error": "Dispute not found."}), 404
    return jsonify(serialize_dispute(ticket, include_events=True)), 200


@admin_dispute_bp.route("/<int:dispute_id>/status", methods=["PUT"])
@token_required(["admin"])
def set_status(dispute_id):
    admin = _get_own_admin()
    ticket = DisputeTicket.query.get(dispute_id)
    if not ticket:
        return jsonify({"error": "Dispute not found."}), 404
    data = request.get_json(force=True) or {}
    try:
        update_status(ticket, data.get("status"), admin.id, data.get("note"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(serialize_dispute(ticket, include_events=True)), 200


@admin_dispute_bp.route("/<int:dispute_id>/resolve", methods=["POST"])
@token_required(["admin"])
def resolve_dispute(dispute_id):
    admin = _get_own_admin()
    ticket = DisputeTicket.query.get(dispute_id)
    if not ticket:
        return jsonify({"error": "Dispute not found."}), 404
    if ticket.status in ("resolved", "rejected"):
        return jsonify({"error": f"Dispute is already '{ticket.status}'."}), 400

    data = request.get_json(force=True) or {}
    refund_amount = data.get("refund_amount")
    if refund_amount is not None:
        try:
            refund_amount = float(refund_amount)
            if refund_amount < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "refund_amount must be a non-negative number."}), 400

    resolve_with_refund(ticket, admin.id, data.get("resolution_note"), refund_amount)
    return jsonify(serialize_dispute(ticket, include_events=True)), 200
