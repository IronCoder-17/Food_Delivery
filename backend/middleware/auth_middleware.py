from functools import wraps
from flask import request, jsonify, g
from backend.utils.auth_utils import decode_token


def token_required(allowed_roles=None):
    """
    Decorator enforcing a valid JWT and (optionally) a role whitelist.
    Usage:
        @token_required()                       -> any authenticated user
        @token_required(["admin"])               -> admin only
        @token_required(["customer","admin"])    -> customer or admin
    This protects backend API routes directly (not just the frontend UI),
    so a customer token can never call restaurant/admin-only endpoints.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401

            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            if allowed_roles and payload.get("role") not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role permissions"}), 403

            g.user_id = payload["user_id"]
            g.role = payload["role"]
            return fn(*args, **kwargs)
        return wrapper
    return decorator
