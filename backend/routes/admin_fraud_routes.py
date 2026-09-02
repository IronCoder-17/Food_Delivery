from flask import Blueprint, request, jsonify, g

from backend.models.models import FraudFlag, Admin
from backend.middleware.auth_middleware import token_required
from backend.services.fraud_service import run_fraud_scan, set_flag_status, serialize_flag

admin_fraud_bp = Blueprint("admin_fraud", __name__, url_prefix="/api/admin/fraud")


def _get_own_admin():
    return Admin.query.filter_by(user_id=g.user_id).first()


@admin_fraud_bp.route("", methods=["GET"])
@token_required(["admin"])
def list_fraud_flags():
    status = request.args.get("status")
    q = FraudFlag.query
    if status:
        q = q.filter_by(status=status)
    flags = q.order_by(FraudFlag.risk_score.desc()).all()
    return jsonify([serialize_flag(f) for f in flags]), 200


@admin_fraud_bp.route("/scan", methods=["POST"])
@token_required(["admin"])
def trigger_scan():
    run_fraud_scan()
    flags = FraudFlag.query.order_by(FraudFlag.risk_score.desc()).all()
    return jsonify({"message": "Scan complete.", "flags": [serialize_flag(f) for f in flags]}), 200


@admin_fraud_bp.route("/<int:flag_id>/status", methods=["PUT"])
@token_required(["admin"])
def update_flag_status(flag_id):
    admin = _get_own_admin()
    flag = FraudFlag.query.get(flag_id)
    if not flag:
        return jsonify({"error": "Flag not found."}), 404
    data = request.get_json(force=True) or {}
    try:
        set_flag_status(flag, data.get("status"), admin.id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(serialize_flag(flag)), 200
