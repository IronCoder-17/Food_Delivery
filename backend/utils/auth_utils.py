import bcrypt
import hashlib
import hmac
import jwt
import secrets
from datetime import datetime, timedelta
from flask import current_app


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def generate_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str):
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_otp(length=6) -> str:
    """
    Cryptographically secure 6-digit numeric OTP using `secrets` (never
    `random`), per the standard `secrets.randbelow(900000) + 100000` pattern
    so the result is always exactly 6 digits with no leading-zero ambiguity.
    """
    if length != 6:
        # Only 6-digit OTPs are used anywhere in this app; keep the function
        # simple and explicit rather than generalizing to arbitrary lengths.
        return "".join(str(secrets.randbelow(10)) for _ in range(length))
    return str(secrets.randbelow(900000) + 100000)


def hash_otp(otp: str) -> str:
    """
    SHA-256 hash of an OTP code, used as the stored/lookup value for
    email-OTP rows. Only this hash is ever persisted -- the raw code exists
    only in the email sent to the customer and briefly in memory on the
    backend while verifying.
    """
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def generate_reset_token() -> str:
    """
    Cryptographically secure, URL-safe password-reset token. Generated with
    `secrets` (not `random`), which is unpredictable enough to be safely
    e-mailed to the customer as a one-time credential.
    """
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """
    SHA-256 hash of a reset token, used as the lookup key in the database.
    Only this hash is ever stored -- the raw token exists only in the
    email sent to the customer and briefly in memory on the backend, so a
    database read alone can never be used to reset an account's password.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a or "", b or "")
