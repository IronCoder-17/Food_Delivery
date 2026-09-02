from flask import Blueprint, request, jsonify

from backend.models.models import db, Referral
from backend.middleware.auth_middleware import token_required
from backend.services.referral_service import get_or_create_referral_config

admin_referral_bp = Blueprint("admin_referral", __name__, url_prefix="/api/admin/referrals")


@admin_referral_bp.route("/config", methods=["GET"])
@token_required(["admin"])
def get_referral_config():
    cfg = get_or_create_referral_config()
    return jsonify({
        "referrer_points": cfg.referrer_points,
        "referred_points": cfg.referred_points,
        "is_active": cfg.is_active,
    }), 200


@admin_referral_bp.route("/config", methods=["PUT"])
@token_required(["admin"])
def update_referral_config():
    cfg = get_or_create_referral_config()
    data = request.get_json(force=True) or {}

    if "referrer_points" in data:
        try:
            val = int(data["referrer_points"])
            if val < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "referrer_points must be a non-negative integer."}), 400
        cfg.referrer_points = val

    if "referred_points" in data:
        try:
            val = int(data["referred_points"])
            if val < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "referred_points must be a non-negative integer."}), 400
        cfg.referred_points = val

    if "is_active" in data:
        cfg.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({
        "referrer_points": cfg.referrer_points,
        "referred_points": cfg.referred_points,
        "is_active": cfg.is_active,
    }), 200


@admin_referral_bp.route("", methods=["GET"])
@token_required(["admin"])
def list_all_referrals():
    referrals = Referral.query.order_by(Referral.created_at.desc()).limit(500).all()
    return jsonify([{
        "id": r.id,
        "referrer_name": f"{r.referrer.first_name} {r.referrer.last_name}" if r.referrer else "Unknown",
        "referred_name": f"{r.referred.first_name} {r.referred.last_name}" if r.referred else "Unknown",
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    } for r in referrals]), 200
