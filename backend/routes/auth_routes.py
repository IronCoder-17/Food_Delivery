import secrets

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_auth_requests
from google.auth.exceptions import GoogleAuthError

from backend.models.models import (
    db, User, Customer, Restaurant, Admin, Cart, Wallet, Notification, PasswordResetToken,
)
from backend.utils.auth_utils import (
    hash_password, verify_password, generate_token, generate_reset_token,
)
from backend.utils.validators import is_valid_email, is_valid_mobile, is_valid_password, is_valid_pincode
from backend.services.otp_service import send_otp, verify_otp
from backend.services.authority_service import assign_default_authorities
from backend.services.loyalty_service import get_or_create_loyalty
from backend.services import referral_service
from backend.services import streak_service

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Reused by the Google-request transport below so we don't build a new one
# per verification call.
_google_auth_request = google_auth_requests.Request()


def _serialize_customer_user(user: "User", customer: "Customer") -> dict:
    """Same response shape as the existing customer_login()/customer_register()
    endpoints, plus a couple of Google-specific hints the frontend needs to
    decide whether to route the customer to profile completion."""
    return {
        "id": user.id,
        "customer_id": customer.id,
        "role": "customer",
        "email": user.email,
        "name": f"{customer.first_name} {customer.last_name}".strip(),
        "auth_provider": customer.auth_provider,
        "profile_completed": bool(customer.profile_completed),
        "needs_profile_completion": not bool(customer.profile_completed),
    }


# ------------------------------------------------------------------
# OTP endpoints (shared by customer registration flow)
# ------------------------------------------------------------------
@auth_bp.route("/otp/send", methods=["POST"])
def send_otp_route():
    data = request.get_json(force=True) or {}
    mobile = (data.get("mobile_number") or "").strip()
    purpose = data.get("purpose", "registration")

    if not is_valid_mobile(mobile):
        return jsonify({"error": "Invalid mobile number."}), 400

    if purpose == "registration" and Customer.query.filter_by(mobile_number=mobile).first():
        return jsonify({"error": "Mobile number already registered."}), 409

    otp, dev_code = send_otp(mobile, purpose)
    resp = {"message": "OTP sent successfully.", "expires_in_minutes": current_app.config["OTP_EXPIRY_MINUTES"]}
    if dev_code:
        resp["dev_otp"] = dev_code  # only present because OTP_DEBUG_MODE=1 (no real SMS gateway configured)
    return jsonify(resp), 200


@auth_bp.route("/otp/verify", methods=["POST"])
def verify_otp_route():
    data = request.get_json(force=True) or {}
    mobile = (data.get("mobile_number") or "").strip()
    code = (data.get("otp_code") or "").strip()
    purpose = data.get("purpose", "registration")

    ok, message = verify_otp(mobile, code, purpose)
    if not ok:
        return jsonify({"error": message}), 400
    return jsonify({"message": message}), 200


# ------------------------------------------------------------------
# Customer registration & login
# ------------------------------------------------------------------
@auth_bp.route("/customer/register", methods=["POST"])
def customer_register():
    data = request.get_json(force=True) or {}
    required = [
        "first_name", "last_name", "email", "password", "confirm_password",
        "mobile_number", "state_id", "city_id", "address", "pincode",
    ]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    mobile = data["mobile_number"].strip()

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format."}), 400
    if not is_valid_mobile(mobile):
        return jsonify({"error": "Invalid mobile number."}), 400
    if not is_valid_pincode(str(data["pincode"])):
        return jsonify({"error": "Invalid pincode."}), 400
    if data["password"] != data["confirm_password"]:
        return jsonify({"error": "Password and confirm password do not match."}), 400
    ok, msg = is_valid_password(data["password"])
    if not ok:
        return jsonify({"error": msg}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409
    if Customer.query.filter_by(mobile_number=mobile).first():
        return jsonify({"error": "Mobile number already registered."}), 409

    # Require OTP verification to have succeeded for this mobile number
    from backend.models.models import OtpVerification
    verified_otp = (
        OtpVerification.query.filter_by(mobile_number=mobile, purpose="registration", is_verified=True)
        .order_by(OtpVerification.id.desc())
        .first()
    )
    if not verified_otp or verified_otp.expires_at < datetime.utcnow() - timedelta(minutes=30):
        return jsonify({"error": "Mobile number is not OTP-verified. Please verify OTP first."}), 400

    user = User(role="customer", email=email, password_hash=hash_password(data["password"]))
    db.session.add(user)
    db.session.flush()

    customer = Customer(
        user_id=user.id,
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        mobile_number=mobile,
        mobile_verified=True,
        state_id=data["state_id"],
        city_id=data["city_id"],
        address=data["address"],
        pincode=str(data["pincode"]),
    )
    db.session.add(customer)
    db.session.flush()

    db.session.add(Cart(customer_id=customer.id))
    db.session.add(Wallet(customer_id=customer.id, balance=0, total_credits=0, total_debits=0))
    db.session.commit()

    # New customers get the default authority configuration (all core
    # permissions ON) and start the loyalty program at Bronze / 0 points.
    assign_default_authorities(customer.id, "customer")
    get_or_create_loyalty(customer.id)

    referral_result = referral_service.apply_referral_code_at_registration(
        customer, data.get("referral_code", "")
    )

    token = generate_token(user.id, "customer")
    response = {
        "message": "Registration successful.",
        "token": token,
        "user": {"id": user.id, "role": "customer", "email": email, "name": f"{customer.first_name} {customer.last_name}"},
    }
    if referral_result.get("warning"):
        response["referral_warning"] = referral_result["warning"]
    return jsonify(response), 201


@auth_bp.route("/customer/login", methods=["POST"])
def customer_login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, role="customer").first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid login credentials."}), 401
    if not user.is_active:
        return jsonify({"error": "This account has been deactivated."}), 403

    customer = Customer.query.filter_by(user_id=user.id).first()
    token = generate_token(user.id, "customer")
    streak_service.record_activity(customer.id, source="login")
    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": {"id": user.id, "customer_id": customer.id, "role": "customer", "email": email,
                  "name": f"{customer.first_name} {customer.last_name}"},
    }), 200


# ------------------------------------------------------------------
# Customer Google Sign-In
# ------------------------------------------------------------------
@auth_bp.route("/customer/google", methods=["POST"])
def customer_google_login():
    data = request.get_json(force=True) or {}
    credential = (data.get("credential") or "").strip()
    if not credential:
        return jsonify({"error": "Missing Google credential."}), 400

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        # Fail loudly for the operator (server log), generically for the client.
        current_app.logger.error("GOOGLE_CLIENT_ID is not configured on the backend.")
        return jsonify({"error": "Google login is not configured on this server."}), 503

    # ---- Verify the credential with Google itself. This checks the JWT's
    # signature against Google's current public keys, its issuer
    # (accounts.google.com / https://accounts.google.com), its audience
    # (must equal our own client_id), and its expiration -- all in one call.
    # We never trust anything in the token until this call succeeds.
    try:
        idinfo = google_id_token.verify_oauth2_token(
            credential, _google_auth_request, client_id
        )
    except (ValueError, GoogleAuthError):
        return jsonify({"error": "Invalid or expired Google credential. Please try again."}), 401
    except Exception:
        current_app.logger.exception("Unexpected error verifying Google credential.")
        return jsonify({"error": "Could not verify Google sign-in. Please try again."}), 502

    issuer = idinfo.get("iss")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        return jsonify({"error": "Invalid Google credential."}), 401

    if not idinfo.get("email_verified"):
        return jsonify({"error": "Your Google email address is not verified. Please verify it with Google first."}), 401

    google_sub = idinfo.get("sub")
    email = (idinfo.get("email") or "").strip().lower()
    if not google_sub or not is_valid_email(email):
        return jsonify({"error": "Google did not return a valid account."}), 401

    given_name = (idinfo.get("given_name") or "").strip()
    family_name = (idinfo.get("family_name") or "").strip()
    if not given_name and not family_name:
        full_name = (idinfo.get("name") or "Customer").strip()
        parts = full_name.split(" ", 1)
        given_name = parts[0]
        family_name = parts[1] if len(parts) > 1 else ""
    picture_url = idinfo.get("picture") or None

    # ---- Case A: this Google account is already linked to a customer. ----
    customer = Customer.query.filter_by(google_id=google_sub).first()
    if customer:
        user = User.query.get(customer.user_id)
        if not user or user.role != "customer":
            return jsonify({"error": "This Google account is not linked to a customer account."}), 403
        if not user.is_active:
            return jsonify({"error": "This account has been deactivated."}), 403
        token = generate_token(user.id, "customer")
        streak_service.record_activity(customer.id, source="login")
        return jsonify({
            "message": "Google login successful.",
            "token": token,
            "user": _serialize_customer_user(user, customer),
        }), 200

    # ---- Case B: an existing user already owns this verified email. ----
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        if existing_user.role != "customer":
            # `email` is unique across every role in this app, so we can't
            # silently create a second account -- and we never want a
            # Google login to hand out restaurant/admin access.
            return jsonify({"error": "This email is already registered to a different type of account."}), 409
        if not existing_user.is_active:
            return jsonify({"error": "This account has been deactivated."}), 403

        customer = Customer.query.filter_by(user_id=existing_user.id).first()
        if not customer:
            return jsonify({"error": "Customer profile not found for this account."}), 404

        # Safely link the Google account to the existing customer -- do NOT
        # create a duplicate. The customer keeps their password login too.
        customer.google_id = google_sub
        db.session.commit()

        token = generate_token(existing_user.id, "customer")
        streak_service.record_activity(customer.id, source="login")
        return jsonify({
            "message": "Google login successful.",
            "token": token,
            "user": _serialize_customer_user(existing_user, customer),
        }), 200

    # ---- Case C: brand-new Google customer. ----
    # We only know verified name/email/picture from Google -- mobile number,
    # state, city, address and pincode are still required by this app and
    # must NOT be invented. The account is created now (so it has a working
    # id/customer_id/JWT and can use the rest of the API), but flagged
    # profile_completed=False until the customer supplies that information
    # via the profile-completion flow.
    user = User(
        role="customer",
        email=email,
        # Google customers don't have a local password. Store a random,
        # never-communicated bcrypt hash so the column stays NOT NULL and
        # the password-login path simply can't match it.
        password_hash=hash_password(secrets.token_urlsafe(32)),
    )
    db.session.add(user)
    db.session.flush()

    # Unique, non-guessable placeholder that can never collide with a real
    # 10-digit Indian mobile number (validated separately by is_valid_mobile),
    # and that clearly identifies incomplete Google sign-ups if inspected.
    placeholder_mobile = f"gg{user.id}{secrets.token_hex(2)}"[:15]

    customer = Customer(
        user_id=user.id,
        first_name=given_name or "Customer",
        last_name=family_name or "",
        mobile_number=placeholder_mobile,
        mobile_verified=False,
        profile_image_url=picture_url,
        google_id=google_sub,
        auth_provider="google",
        profile_completed=False,
    )
    db.session.add(customer)
    db.session.flush()

    # Same bootstrap as a normal registration, so every other customer
    # route (cart, wallet, authorities, loyalty) works immediately.
    db.session.add(Cart(customer_id=customer.id))
    db.session.add(Wallet(customer_id=customer.id, balance=0, total_credits=0, total_debits=0))
    db.session.commit()

    assign_default_authorities(customer.id, "customer")
    get_or_create_loyalty(customer.id)

    token = generate_token(user.id, "customer")
    return jsonify({
        "message": "Google login successful.",
        "token": token,
        "user": _serialize_customer_user(user, customer),
    }), 201


# ------------------------------------------------------------------
# Restaurant registration & login
# ------------------------------------------------------------------
@auth_bp.route("/restaurant/register", methods=["POST"])
def restaurant_register():
    data = request.get_json(force=True) or {}
    required = [
        "restaurant_name", "owner_name", "email", "password", "confirm_password",
        "mobile_number", "address", "state_id", "city_id", "pincode",
    ]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format."}), 400
    if not is_valid_mobile(data["mobile_number"]):
        return jsonify({"error": "Invalid mobile number."}), 400
    if data["password"] != data["confirm_password"]:
        return jsonify({"error": "Password and confirm password do not match."}), 400
    ok, msg = is_valid_password(data["password"])
    if not ok:
        return jsonify({"error": msg}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(role="restaurant", email=email, password_hash=hash_password(data["password"]))
    db.session.add(user)
    db.session.flush()

    restaurant = Restaurant(
        user_id=user.id,
        restaurant_name=data["restaurant_name"].strip(),
        owner_name=data["owner_name"].strip(),
        mobile_number=data["mobile_number"].strip(),
        address=data["address"],
        state_id=data["state_id"],
        city_id=data["city_id"],
        pincode=str(data["pincode"]),
        description=data.get("description", ""),
        logo_url=data.get("logo_url", ""),
        cover_image_url=data.get("cover_image_url", ""),
        document_url=data.get("document_url", ""),
        opening_time=data.get("opening_time", "09:00"),
        closing_time=data.get("closing_time", "23:00"),
        status="pending",
    )
    db.session.add(restaurant)
    db.session.commit()

    # New restaurants get the default authority configuration (all core
    # permissions ON, admin can restrict individual ones later).
    assign_default_authorities(restaurant.id, "restaurant")

    # notify admins of a new restaurant application
    for admin in Admin.query.all():
        db.session.add(Notification(
            recipient_role="admin", recipient_id=admin.id,
            title="New Restaurant Application",
            message=f"{restaurant.restaurant_name} has applied and is pending approval.",
        ))
    db.session.commit()

    return jsonify({
        "message": "Restaurant application submitted. Your account is pending admin approval.",
        "restaurant_id": restaurant.id,
        "status": "pending",
    }), 201


@auth_bp.route("/restaurant/login", methods=["POST"])
def restaurant_login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, role="restaurant").first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid login credentials."}), 401

    restaurant = Restaurant.query.filter_by(user_id=user.id).first()
    if restaurant.status == "pending":
        return jsonify({"error": "Your restaurant account is pending admin approval."}), 403
    if restaurant.status in ("rejected", "deactivated"):
        return jsonify({"error": f"Your restaurant account is {restaurant.status}. Contact support."}), 403
    if not user.is_active:
        return jsonify({"error": "This account has been deactivated."}), 403

    token = generate_token(user.id, "restaurant")
    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": {"id": user.id, "restaurant_id": restaurant.id, "role": "restaurant", "email": email,
                  "name": restaurant.restaurant_name},
    }), 200


# ------------------------------------------------------------------
# Admin login (not publicly linked from customer UI)
# ------------------------------------------------------------------
@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, role="admin").first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid login credentials."}), 401
    if not user.is_active:
        return jsonify({"error": "This account has been deactivated."}), 403

    admin = Admin.query.filter_by(user_id=user.id).first()
    token = generate_token(user.id, "admin")
    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": {"id": user.id, "admin_id": admin.id, "role": "admin", "email": email, "name": admin.name},
    }), 200


# ------------------------------------------------------------------
# Forgot password (works for any role, via email)
# ------------------------------------------------------------------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()

    # Always return a generic message so we don't leak which emails exist
    generic = {"message": "If that email is registered, a password reset link has been sent."}
    if not user:
        return jsonify(generic), 200

    token = generate_reset_token()
    reset = PasswordResetToken(
        user_id=user.id, token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.session.add(reset)
    db.session.commit()

    # TODO: email this link via a real mail provider. Returned here only
    # because no SMTP/email service is configured in this environment.
    print(f"[DEV RESET LINK] /reset-password?token={token}")
    resp = dict(generic)
    if current_app.config["OTP_DEBUG_MODE"]:
        resp["dev_reset_token"] = token
    return jsonify(resp), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(force=True) or {}
    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400
    ok, msg = is_valid_password(new_password or "")
    if not ok:
        return jsonify({"error": msg}), 400

    reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset or reset.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired reset token."}), 400

    user = User.query.get(reset.user_id)
    user.password_hash = hash_password(new_password)
    reset.used = True
    db.session.commit()
    return jsonify({"message": "Password reset successful. Please log in."}), 200
