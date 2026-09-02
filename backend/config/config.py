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

    # OTP is simulated (no SMS gateway configured). In DEBUG mode the OTP
    # code is returned in the API response (dev_otp field) so you can test
    # the flow end-to-end without a real SMS provider. Wire a real provider
    # (Twilio / MSG91 / etc.) in backend/services/otp_service.py when ready.
    OTP_DEBUG_MODE = os.environ.get("OTP_DEBUG_MODE", "1") == "1"
    OTP_EXPIRY_MINUTES = 5
    OTP_MAX_ATTEMPTS = 5
