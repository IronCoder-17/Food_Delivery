from flask import Blueprint, request, jsonify, g
from backend.models.models import db, Customer, Admin, LoyaltyLevel, CustomerLoyalty, LoyaltyTransaction
from backend.middleware.auth_middleware import token_required
from backend.services import loyalty_service

admin_loyalty_bp = Blueprint("admin_loyalty", __name__, url_prefix="/api/admin/loyalty")


def _admin_id():
    admin = Admin.query.filter_by(user_id=g.user_id).first()
    return admin.id if admin else None


# ---------------------------- Customer loyalty listing ----------------------------
@admin_loyalty_bp.route("/customers", methods=["GET"])
@token_required(["admin"])
def list_customer_loyalty():
    search = request.args.get("search")
    rank = request.args.get("rank")
    min_points = request.args.get("min_points", type=int)
    max_points = request.args.get("max_points", type=int)

    q = db.session.query(Customer, CustomerLoyalty).outerjoin(
        CustomerLoyalty, CustomerLoyalty.customer_id == Customer.id
    )
    if search:
        like = f"%{search}%"
        q = q.filter((Customer.first_name.ilike(like)) | (Customer.last_name.ilike(like)))
    rows = q.all()

    results = []
    for customer, loyalty in rows:
        if not loyalty:
            loyalty = loyalty_service.get_or_create_loyalty(customer.id)
        if rank and loyalty.rank != rank:
            continue
        if min_points is not None and loyalty.points < min_points:
            continue
        if max_points is not None and loyalty.points > max_points:
            continue
        results.append({
            "customer_id": customer.id,
            "name": f"{customer.first_name} {customer.last_name}",
            "email": customer.user.email,
            "total_orders": loyalty.total_orders,
            "total_spending": float(loyalty.total_spending or 0),
            "points": loyalty.points,
            "lifetime_points": loyalty.lifetime_points,
            "rank": loyalty.rank,
            "updated_at": loyalty.updated_at.isoformat() if loyalty.updated_at else None,
        })
    results.sort(key=lambda r: r["points"], reverse=True)
    return jsonify(results), 200


@admin_loyalty_bp.route("/customer/<int:customer_id>", methods=["GET"])
@token_required(["admin"])
def get_customer_loyalty_detail(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found."}), 404
    loyalty = loyalty_service.get_or_create_loyalty(customer.id)
    txns = (
        LoyaltyTransaction.query.filter_by(customer_id=customer.id)
        .order_by(LoyaltyTransaction.created_at.desc()).limit(100).all()
    )
    summary = loyalty_service.serialize_loyalty_summary(loyalty)
    summary["customer_id"] = customer.id
    summary["name"] = f"{customer.first_name} {customer.last_name}"
    summary["email"] = customer.user.email
    summary["transactions"] = [loyalty_service.serialize_transaction(t) for t in txns]
    return jsonify(summary), 200


@admin_loyalty_bp.route("/customer/<int:customer_id>/adjust", methods=["POST"])
@token_required(["admin"])
def adjust_customer_points(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    data = request.get_json(force=True) or {}
    delta = data.get("delta")
    reason = (data.get("reason") or "").strip()

    if delta is None:
        return jsonify({"error": "delta (positive to add, negative to remove) is required."}), 400
    try:
        delta = int(delta)
    except (TypeError, ValueError):
        return jsonify({"error": "delta must be an integer."}), 400
    if delta == 0:
        return jsonify({"error": "delta cannot be zero."}), 400
    if not reason:
        return jsonify({"error": "A reason is required for manual point adjustments."}), 400

    loyalty, txn, previous_points, level = loyalty_service.admin_adjust_points(
        customer.id, delta, reason, _admin_id(),
    )
    return jsonify({
        "message": "Points adjusted.",
        "previous_points": previous_points,
        "delta": delta,
        "new_points": loyalty.points,
        "new_rank": loyalty.rank,
        "transaction": loyalty_service.serialize_transaction(txn),
    }), 200


# ---------------------------- Loyalty level (rank) configuration ----------------------------
@admin_loyalty_bp.route("/levels", methods=["GET"])
@token_required(["admin"])
def list_levels():
    levels = loyalty_service.get_levels_ordered()
    return jsonify([loyalty_service.serialize_level(l) for l in levels]), 200


def _validate_no_overlap(levels, changed_id, new_min, new_max):
    for lvl in levels:
        if lvl.id == changed_id:
            continue
        lvl_max = lvl.maximum_points if lvl.maximum_points is not None else float("inf")
        new_max_val = new_max if new_max is not None else float("inf")
        # ranges overlap if new_min <= lvl_max and lvl.minimum_points <= new_max_val
        if new_min <= lvl_max and lvl.minimum_points <= new_max_val:
            return False, lvl.name
    return True, None


@admin_loyalty_bp.route("/levels/<int:level_id>", methods=["PUT"])
@token_required(["admin"])
def update_level(level_id):
    level = LoyaltyLevel.query.get(level_id)
    if not level:
        return jsonify({"error": "Loyalty level not found."}), 404

    data = request.get_json(force=True) or {}
    new_min = data.get("minimum_points", level.minimum_points)
    new_max = data.get("maximum_points", level.maximum_points)

    try:
        new_min = int(new_min)
        new_max = int(new_max) if new_max is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "minimum_points/maximum_points must be integers."}), 400

    if new_max is not None and new_max < new_min:
        return jsonify({"error": "maximum_points cannot be less than minimum_points."}), 400

    other_levels = LoyaltyLevel.query.filter(LoyaltyLevel.id != level_id).all()
    ok, clash_name = _validate_no_overlap(other_levels, level_id, new_min, new_max)
    if not ok:
        return jsonify({"error": f"This range overlaps with '{clash_name}'. Ranges must not overlap."}), 400

    if "name" in data and data["name"]:
        name = data["name"].strip()
        clash = LoyaltyLevel.query.filter(LoyaltyLevel.name == name, LoyaltyLevel.id != level_id).first()
        if clash:
            return jsonify({"error": "Another rank already uses this name."}), 400
        level.name = name
    if "benefits" in data:
        level.benefits = data["benefits"]
    if "description" in data:
        level.description = data["description"]
    if "is_active" in data:
        level.is_active = bool(data["is_active"])

    level.minimum_points = new_min
    level.maximum_points = new_max
    db.session.commit()

    updated_count = loyalty_service.recalculate_all_ranks()

    return jsonify({
        "message": "Loyalty level updated.",
        "level": loyalty_service.serialize_level(level),
        "customers_rank_recalculated": updated_count,
    }), 200
