import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME", "food_delivery")

    if DB_HOST and DB_USER:
        # Real MySQL connection, e.g. set these in your .env:
        # DB_HOST=your-mysql-host DB_PORT=3306 DB_USER=... DB_PASSWORD=... DB_NAME=food_delivery
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            f"?charset=utf8mb4"
        )
    else:
        # Local/dev fallback only, used when no MySQL credentials are configured
        # (e.g. running `python app.py` on a laptop without MySQL set up yet).
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "dev_fallback.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Google Sign-In (customer login) ----
    # Same Client ID as the frontend's VITE_GOOGLE_CLIENT_ID -- the backend
    # uses it to verify that a Google credential was actually issued for
    # THIS app (the "audience" check) before trusting anything in it.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

    DELIVERY_FEE = float(os.environ.get("DELIVERY_FEE", "40"))

    # Mobile-SMS OTP is still simulated (no SMS gateway configured -- see
    # backend/services/otp_service.py). In DEBUG mode the OTP code is
    # returned in the API response (dev_otp field) so the mobile-verification
    # step can be tested without a real SMS provider. Wire a real provider
    # (Twilio / MSG91 / etc.) there when ready.
    #
    # Email OTP (registration email verification + forgot password) is REAL
    # -- see backend/services/email_otp_service.py -- and shares these same
    # expiry/attempt-limit settings.
    OTP_DEBUG_MODE = os.environ.get("OTP_DEBUG_MODE", "1") == "1"
    OTP_EXPIRY_MINUTES = int(os.environ.get("OTP_EXPIRY_MINUTES", "5"))
    OTP_MAX_ATTEMPTS = int(os.environ.get("OTP_MAX_ATTEMPTS", "5"))
    # Minimum seconds between OTP (re)send requests for the same email +
    # purpose, enforced on the backend so a customer (or an attacker) can't
    # trigger unlimited emails.
    OTP_RESEND_COOLDOWN = int(os.environ.get("OTP_RESEND_COOLDOWN", "30"))

    # ---- Password reset email ----
    # Public frontend origin used to build the reset link e-mailed to the
    # customer, e.g. http://localhost:5173 in dev or https://app.yoursite.com
    # in production. Safe to expose -- it's just a URL, not a secret.
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    # EMAIL_ENABLED=0 (default) skips the real SMTP call and just logs what
    # would have been sent, so the reset flow can be tested end-to-end
    # without SMTP credentials. Set EMAIL_ENABLED=1 once MAIL_* below are
    # configured with a real (or Gmail App Password) SMTP account.
    EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "0") == "1"

    # ---- SMTP configuration (backend only -- NEVER read by the frontend) ----
    # For Gmail: MAIL_HOST=smtp.gmail.com, MAIL_PORT=587, MAIL_USE_TLS=1,
    # MAIL_USERNAME=you@gmail.com, MAIL_PASSWORD=<16-char App Password>.
    # A Gmail App Password requires 2-Step Verification to be enabled on the
    # Google account -- see README.md for full setup steps. Do not use the
    # normal Gmail account password here.
    MAIL_HOST = os.environ.get("MAIL_HOST", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587") or 587)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_FROM_EMAIL = os.environ.get("MAIL_FROM_EMAIL", MAIL_USERNAME)
    MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "QuickBite")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "1") == "1"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "0") == "1"

    # Minimum seconds a customer must wait before another reset email can be
    # requested for the *same* email address, enforced on the backend (not
    # just the frontend) so repeated requests can't spam a real inbox.
    PASSWORD_RESET_COOLDOWN_SECONDS = int(os.environ.get("PASSWORD_RESET_COOLDOWN_SECONDS", "60"))
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = int(os.environ.get("PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", "30"))
    # Short-lived authorization token issued immediately after a customer
    # verifies their forgot-password OTP -- used once, right away, to submit
    # the new password. Deliberately shorter than the old link-based expiry
    # above since the customer is already mid-flow when it's issued.
    OTP_RESET_TOKEN_EXPIRY_MINUTES = int(os.environ.get("OTP_RESET_TOKEN_EXPIRY_MINUTES", "10"))
