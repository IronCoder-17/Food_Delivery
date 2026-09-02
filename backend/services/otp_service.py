from datetime import datetime, timedelta
from flask import current_app
from backend.models.models import db, OtpVerification
from backend.utils.auth_utils import generate_otp


def send_otp(mobile_number: str, purpose: str = "registration"):
    """
    Generates and 'sends' an OTP. No real SMS gateway is configured, so in
    OTP_DEBUG_MODE the code is returned to the caller so the flow can be
    tested end-to-end. To go live, replace the body of this function with
    a call to your SMS provider (Twilio/MSG91/etc.) and stop returning the
    raw code from the API layer.
    """
    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])

    otp = OtpVerification(
        mobile_number=mobile_number,
        otp_code=code,
        purpose=purpose,
        expires_at=expires_at,
    )
    db.session.add(otp)
    db.session.commit()

    # TODO: integrate real SMS provider here.
    print(f"[DEV OTP] mobile={mobile_number} purpose={purpose} code={code}")

    return otp, (code if current_app.config["OTP_DEBUG_MODE"] else None)


def verify_otp(mobile_number: str, code: str, purpose: str = "registration"):
    otp = (
        OtpVerification.query.filter_by(mobile_number=mobile_number, purpose=purpose, is_verified=False)
        .order_by(OtpVerification.id.desc())
        .first()
    )
    if not otp:
        return False, "No OTP request found. Please request a new OTP."

    if otp.expires_at < datetime.utcnow():
        return False, "OTP expired. Please request a new OTP."

    if otp.attempts >= current_app.config["OTP_MAX_ATTEMPTS"]:
        return False, "Maximum OTP attempts exceeded. Please request a new OTP."

    otp.attempts += 1
    db.session.commit()

    if otp.otp_code != code:
        return False, "Invalid OTP."

    otp.is_verified = True
    db.session.commit()
    return True, "OTP verified successfully."
