from flask import Blueprint, jsonify, g

from backend.models.models import Customer, Referral
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.referral_service import get_or_create_referral_code, get_or_create_referral_config, serialize_referral

referral_bp = Blueprint("referral", __name__, url_prefix="/api/customer/referrals")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


@referral_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.referrals")
def my_referrals():
    customer = _get_own_customer()
    code = get_or_create_referral_code(customer)
    cfg = get_or_create_referral_config()

    referrals = Referral.query.filter_by(referrer_customer_id=customer.id).order_by(Referral.created_at.desc()).all()
    completed = [r for r in referrals if r.status == "completed"]

    return jsonify({
        "referral_code": code,
        "referrer_reward_points": cfg.referrer_points,
        "referred_reward_points": cfg.referred_points,
        "rewards_active": cfg.is_active,
        "total_referrals": len(referrals),
        "completed_referrals": len(completed),
        "points_earned_from_referrals": len(completed) * cfg.referrer_points,
        "referrals": [serialize_referral(r, customer.id) for r in referrals],
    }), 200
