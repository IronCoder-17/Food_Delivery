import re

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
MOBILE_RE = re.compile(r"^[6-9]\d{9}$")  # Indian mobile numbers


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email))


def is_valid_mobile(mobile: str) -> bool:
    return bool(mobile) and bool(MOBILE_RE.match(mobile))


def is_valid_password(password: str) -> (bool, str):
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""


def is_valid_pincode(pincode: str) -> bool:
    return bool(pincode) and bool(re.match(r"^\d{6}$", pincode))
