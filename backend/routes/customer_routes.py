from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Customer, OtpVerification
from backend.middleware.auth_middleware import token_required
from backend.utils.validators import is_valid_mobile, is_valid_pincode
from backend.services.authority_service import require_permission

customer_bp = Blueprint("customer", __name__, url_prefix="/api/customer")

VALID_GENDERS = {"male", "female", "other", "prefer_not_to_say"}


def _get_own_customer():
    # The customer is always resolved from the authenticated user's token
    # (g.user_id), never from a client-supplied id, so a customer can only
    # ever see/edit their own profile.
    return Customer.query.filter_by(user_id=g.user_id).first()


def _serialize_customer(c: Customer):
    return {
        "id": c.id,
        "user_id": c.user_id,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "email": c.user.email,
        "mobile_number": c.mobile_number,
        "mobile_verified": c.mobile_verified,
        "date_of_birth": c.date_of_birth.isoformat() if c.date_of_birth else None,
        "gender": c.gender,
        "address": c.address,
        "state_id": c.state_id,
        "city_id": c.city_id,
        "pincode": c.pincode,
        "profile_image_url": c.profile_image_url,
        "is_active": c.user.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "auth_provider": c.auth_provider,
        "profile_completed": bool(c.profile_completed),
    }


@customer_bp.route("/profile", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.view_profile")
def get_profile():
    c = _get_own_customer()
    if not c:
        return jsonify({"error": "Customer profile not found."}), 404
    return jsonify(_serialize_customer(c)), 200


@customer_bp.route("/profile", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.edit_profile")
def update_profile():
    c = _get_own_customer()
    if not c:
        return jsonify({"error": "Customer profile not found."}), 404

    data = request.get_json(force=True) or {}

    if "first_name" in data:
        first_name = (data["first_name"] or "").strip()
        if not first_name:
            return jsonify({"error": "First name cannot be empty."}), 400
        c.first_name = first_name

    if "last_name" in data:
        last_name = (data["last_name"] or "").strip()
        if not last_name:
            return jsonify({"error": "Last name cannot be empty."}), 400
        c.last_name = last_name

    if "mobile_number" in data and data["mobile_number"]:
        mobile = str(data["mobile_number"]).strip()
        if not is_valid_mobile(mobile):
            return jsonify({"error": "Invalid mobile number."}), 400
        if mobile != c.mobile_number and Customer.query.filter_by(mobile_number=mobile).first():
            return jsonify({"error": "Mobile number already in use."}), 409
        if mobile != c.mobile_number:
            c.mobile_verified = False
        c.mobile_number = mobile

    if "date_of_birth" in data:
        raw_dob = data["date_of_birth"]
        if not raw_dob:
            c.date_of_birth = None
        else:
            try:
                c.date_of_birth = datetime.strptime(raw_dob, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid date of birth format. Use YYYY-MM-DD."}), 400

    if "gender" in data:
        gender = (data["gender"] or "").strip().lower()
        if gender and gender not in VALID_GENDERS:
            return jsonify({"error": "Invalid gender value."}), 400
        c.gender = gender or None

    if "address" in data:
        c.address = data["address"]

    if "pincode" in data and data["pincode"]:
        pincode = str(data["pincode"]).strip()
        if not is_valid_pincode(pincode):
            return jsonify({"error": "Invalid pincode."}), 400
        c.pincode = pincode

    if "state_id" in data:
        c.state_id = data["state_id"] or None

    if "city_id" in data:
        c.city_id = data["city_id"] or None

    if "profile_image_url" in data:
        c.profile_image_url = data["profile_image_url"]

    db.session.commit()
    return jsonify({"message": "Profile updated successfully.", "customer": _serialize_customer(c)}), 200


# ------------------------------------------------------------------
# Google Customer Profile Completion
# ------------------------------------------------------------------
# A brand-new Google sign-up (see backend/routes/auth_routes.py ->
# customer_google_login) already has a working, authenticated customer
# account, but Google never gives us mobile number / state / city / address
# / pincode. This endpoint is the only way to fill those in and flip
# profile_completed to True. It's separate from the general update_profile()
# above because it's a one-time, all-required-fields step that also demands
# a freshly OTP-verified mobile number, exactly like normal registration.
@customer_bp.route("/complete-profile", methods=["POST"])
@token_required(["customer"])
def complete_profile():
    c = _get_own_customer()
    if not c:
        return jsonify({"error": "Customer profile not found."}), 404

    if c.profile_completed:
        return jsonify({"message": "Profile is already complete.", "customer": _serialize_customer(c)}), 200

    data = request.get_json(force=True) or {}
    required = ["mobile_number", "state_id", "city_id", "address", "pincode"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    mobile = str(data["mobile_number"]).strip()
    if not is_valid_mobile(mobile):
        return jsonify({"error": "Invalid mobile number."}), 400
    if not is_valid_pincode(str(data["pincode"])):
        return jsonify({"error": "Invalid pincode."}), 400
    if Customer.query.filter(Customer.mobile_number == mobile, Customer.id != c.id).first():
        return jsonify({"error": "Mobile number already registered to another account."}), 409

    # Require OTP verification for this mobile number, same as normal
    # registration -- Google verifies the customer's email, not their phone.
    verified_otp = (
        OtpVerification.query.filter_by(mobile_number=mobile, purpose="registration", is_verified=True)
        .order_by(OtpVerification.id.desc())
        .first()
    )
    if not verified_otp or verified_otp.expires_at < datetime.utcnow() - timedelta(minutes=30):
        return jsonify({"error": "Mobile number is not OTP-verified. Please verify OTP first."}), 400

    if "first_name" in data and data["first_name"]:
        c.first_name = data["first_name"].strip()
    if "last_name" in data and data["last_name"]:
        c.last_name = data["last_name"].strip()

    c.mobile_number = mobile
    c.mobile_verified = True
    c.state_id = data["state_id"]
    c.city_id = data["city_id"]
    c.address = data["address"]
    c.pincode = str(data["pincode"])
    c.profile_completed = True

    db.session.commit()
    return jsonify({
        "message": "Profile completed successfully.",
        "customer": _serialize_customer(c),
    }), 200
