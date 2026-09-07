"""
Real email-OTP service backing registration email verification and the
forgot-password flow. Reuses the existing `otp_verifications` table (the
same one the mobile-SMS flow in otp_service.py uses) rather than creating a
duplicate table -- rows are distinguished by which columns are populated
(`mobile_number`/`otp_code` for SMS, `email`/`otp_hash` for email).

Only a SHA-256 hash of the OTP is ever stored. The raw code exists only:
  - briefly in memory while this module builds/sends it, and
  - in the email delivered to the customer's inbox.
It is never logged, never returned by any API response when EMAIL_ENABLED=1,
and never stored in plaintext.
"""

from datetime import datetime, timedelta

from flask import current_app

from backend.models.models import db, OtpVerification
from backend.utils.auth_utils import generate_otp, hash_otp, constant_time_compare
from backend.services.email_service import send_otp_email

# Generic, non-enumerating messages -- callers should surface these as-is.
GENERIC_SENT_MESSAGE = "If an account exists with this email, an OTP has been sent."
GENERIC_COOLDOWN_MESSAGE = "An OTP was already sent recently. Please check your inbox, or try again shortly."


def _latest_row(email: str, purpose: str):
    return (
        OtpVerification.query.filter_by(email=email, purpose=purpose)
        .order_by(OtpVerification.id.desc())
        .first()
    )


def send_email_otp(email: str, purpose: str) -> tuple[bool, str, str | None]:
    """
    Generates, stores (hashed), and emails a fresh OTP for (email, purpose).

    Returns (sent, message, internal_error):
      - sent=True + generic message: caller should return this to the
        customer regardless of whether the address exists (enumeration-safe
        callers, e.g. forgot-password, decide that upstream by not calling
        this at all for unregistered emails -- see auth_routes.py).
      - sent=False + internal_error: SMTP or config failure. `message` is
        still a safe, customer-facing string; `internal_error` is for logs
        only and must never be shown to the customer.

    Enforces, all on the backend (never trusting the frontend):
      - a resend cooldown (OTP_RESEND_COOLDOWN seconds) per (email, purpose)
      - invalidation of any still-valid previous OTP for the same
        (email, purpose) so only the newest code ever works
    """
    cooldown_seconds = current_app.config["OTP_RESEND_COOLDOWN"]
    recent_cutoff = datetime.utcnow() - timedelta(seconds=cooldown_seconds)

    last_row = _latest_row(email, purpose)
    if last_row and last_row.created_at and last_row.created_at >= recent_cutoff:
        # Don't send another email yet, but this is still a "success" from
        # the customer's point of view -- they already have a valid code.
        return True, GENERIC_COOLDOWN_MESSAGE, None

    expiry_minutes = current_app.config["OTP_EXPIRY_MINUTES"]
    raw_otp = generate_otp()
    row = OtpVerification(
        email=email,
        otp_hash=hash_otp(raw_otp),
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )
    db.session.add(row)
    db.session.commit()

    sent, internal_error = send_otp_email(email, raw_otp, purpose, expiry_minutes)
    if not sent:
        # Don't leave a "valid-looking" but never-emailed OTP in the
        # database -- delete it so it can't be brute-forced or confused
        # with a code the customer never actually received.
        db.session.delete(row)
        db.session.commit()
        return False, "Unable to send OTP right now. Please try again shortly.", internal_error

    return True, GENERIC_SENT_MESSAGE, None


def verify_email_otp(email: str, code: str, purpose: str) -> tuple[bool, str]:
    """
    Verifies a submitted OTP against the latest unverified row for
    (email, purpose). Enforces expiry and a max-attempts lockout, and marks
    the row verified (single-use) on success.
    """
    row = (
        OtpVerification.query.filter_by(email=email, purpose=purpose, is_verified=False)
        .order_by(OtpVerification.id.desc())
        .first()
    )
    if not row or not row.otp_hash:
        return False, "No OTP request found. Please request a new OTP."

    if row.expires_at < datetime.utcnow():
        return False, "OTP expired. Please request a new OTP."

    max_attempts = current_app.config["OTP_MAX_ATTEMPTS"]
    if row.attempts >= max_attempts:
        return False, "Too many incorrect attempts. Please request a new OTP."

    row.attempts += 1
    db.session.commit()

    if not constant_time_compare(row.otp_hash, hash_otp(code or "")):
        remaining = max(max_attempts - row.attempts, 0)
        if remaining <= 0:
            return False, "Too many incorrect attempts. Please request a new OTP."
        return False, "Invalid OTP."

    row.is_verified = True
    db.session.commit()
    return True, "OTP verified successfully."
