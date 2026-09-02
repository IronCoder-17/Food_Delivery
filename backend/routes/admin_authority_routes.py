from flask import Blueprint, request, jsonify, g
from backend.models.models import db, Customer, Restaurant, Admin, AuthorityPermission, UserAuthority, AuthorityAuditLog
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import (
    get_effective_authorities, set_authority, serialize_permission,
)

admin_authority_bp = Blueprint("admin_authority", __name__, url_prefix="/api/admin/authorities")


def _admin_id():
    admin = Admin.query.filter_by(user_id=g.user_id).first()
    return admin.id if admin else None


# ---------------------------- Permission catalog ----------------------------
@admin_authority_bp.route("/permissions", methods=["GET"])
@token_required(["admin"])
def list_permissions():
    user_type = request.args.get("user_type")
    q = AuthorityPermission.query
    if user_type:
        q = q.filter_by(user_type=user_type)
    perms = q.order_by(AuthorityPermission.user_type, AuthorityPermission.permission_name).all()
    return jsonify([serialize_permission(p) for p in perms]), 200


# ---------------------------- Customer authorities ----------------------------
@admin_authority_bp.route("/customers", methods=["GET"])
@token_required(["admin"])
def list_customer_authorities():
    search = request.args.get("search")
    q = Customer.query
    if search:
        like = f"%{search}%"
        q = q.filter((Customer.first_name.ilike(like)) | (Customer.last_name.ilike(like)) | (Customer.mobile_number.ilike(like)))
    customers = q.order_by(Customer.first_name).all()
    return jsonify([{
        "id": c.id, "name": f"{c.first_name} {c.last_name}", "email": c.user.email,
        "is_active": c.user.is_active,
    } for c in customers]), 200


@admin_authority_bp.route("/customer/<int:customer_id>", methods=["GET"])
@token_required(["admin"])
def get_customer_authority(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found."}), 404
    return jsonify({
        "customer_id": customer.id,
        "name": f"{customer.first_name} {customer.last_name}",
        "email": customer.user.email,
        "authorities": get_effective_authorities(customer.id, "customer"),
    }), 200


@admin_authority_bp.route("/customer/<int:customer_id>", methods=["PUT"])
@token_required(["admin"])
def update_customer_authority(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    data = request.get_json(force=True) or {}
    permission_key = data.get("permission_key")
    is_allowed = data.get("is_allowed")
    reason = data.get("reason", "")

    if not permission_key or is_allowed is None:
        return jsonify({"error": "permission_key and is_allowed are required."}), 400

    try:
        previous, new = set_authority(customer.id, "customer", permission_key, bool(is_allowed), _admin_id(), reason)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Authority updated.", "permission_key": permission_key,
        "previous_status": previous, "new_status": new,
    }), 200


# ---------------------------- Restaurant authorities ----------------------------
@admin_authority_bp.route("/restaurants", methods=["GET"])
@token_required(["admin"])
def list_restaurant_authorities():
    search = request.args.get("search")
    q = Restaurant.query
    if search:
        q = q.filter(Restaurant.restaurant_name.ilike(f"%{search}%"))
    restaurants = q.order_by(Restaurant.restaurant_name).all()
    return jsonify([{
        "id": r.id, "name": r.restaurant_name, "email": r.user.email, "status": r.status,
    } for r in restaurants]), 200


@admin_authority_bp.route("/restaurant/<int:restaurant_id>", methods=["GET"])
@token_required(["admin"])
def get_restaurant_authority(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found."}), 404
    return jsonify({
        "restaurant_id": restaurant.id,
        "name": restaurant.restaurant_name,
        "email": restaurant.user.email,
        "authorities": get_effective_authorities(restaurant.id, "restaurant"),
    }), 200


@admin_authority_bp.route("/restaurant/<int:restaurant_id>", methods=["PUT"])
@token_required(["admin"])
def update_restaurant_authority(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found."}), 404

    data = request.get_json(force=True) or {}
    permission_key = data.get("permission_key")
    is_allowed = data.get("is_allowed")
    reason = data.get("reason", "")

    if not permission_key or is_allowed is None:
        return jsonify({"error": "permission_key and is_allowed are required."}), 400

    try:
        previous, new = set_authority(restaurant.id, "restaurant", permission_key, bool(is_allowed), _admin_id(), reason)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Authority updated.", "permission_key": permission_key,
        "previous_status": previous, "new_status": new,
    }), 200


# ---------------------------- Audit log ----------------------------
@admin_authority_bp.route("/audit-logs", methods=["GET"])
@token_required(["admin"])
def audit_logs():
    user_type = request.args.get("user_type")
    user_id = request.args.get("user_id", type=int)
    q = AuthorityAuditLog.query
    if user_type:
        q = q.filter_by(user_type=user_type)
    if user_id:
        q = q.filter_by(user_id=user_id)
    logs = q.order_by(AuthorityAuditLog.created_at.desc()).limit(200).all()

    admin_ids = {l.admin_id for l in logs if l.admin_id}
    admins = {a.id: a.name for a in Admin.query.filter(Admin.id.in_(admin_ids)).all()} if admin_ids else {}

    return jsonify([{
        "id": l.id, "admin_id": l.admin_id, "admin_name": admins.get(l.admin_id, "System"),
        "user_id": l.user_id, "user_type": l.user_type, "permission": l.permission,
        "previous_status": l.previous_status, "new_status": l.new_status,
        "reason": l.reason, "created_at": l.created_at.isoformat(),
    } for l in logs]), 200
