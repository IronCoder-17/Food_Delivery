from datetime import datetime
from flask import Blueprint, request, jsonify, g
from backend.models.models import (
    db, User, Customer, Restaurant, Food, Category, Order, Payment, Wallet, WalletTransaction,
    GameQuestion, GameSession, Notification,
)
from backend.middleware.auth_middleware import token_required
from backend.routes.food_routes import serialize_food
from backend.routes.order_routes import _serialize_order

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ---------------------------- Dashboard ----------------------------
@admin_bp.route("/dashboard", methods=["GET"])
@token_required(["admin"])
def dashboard():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_customers = Customer.query.count()
    total_restaurants = Restaurant.query.count()
    pending_restaurants = Restaurant.query.filter_by(status="pending").count()
    total_foods = Food.query.count()
    all_orders = Order.query.all()
    today_orders = [o for o in all_orders if o.created_at >= today_start]
    total_revenue = sum(float(o.total_amount) for o in all_orders if o.payment_status == "paid")
    wallet_bonuses = sum(float(t.amount) for t in WalletTransaction.query.filter_by(reference_type="game_reward").all())
    active_users = User.query.filter_by(is_active=True).count()

    payment_stats = {
        "razorpay": Payment.query.filter_by(method="razorpay", status="success").count(),
        "cod": Payment.query.filter_by(method="cod").count(),
        "wallet": Payment.query.filter_by(method="wallet", status="success").count(),
        "failed": Payment.query.filter_by(status="failed").count(),
        "pending": Payment.query.filter_by(status="pending").count(),
    }

    return jsonify({
        "total_customers": total_customers,
        "total_restaurants": total_restaurants,
        "pending_restaurants": pending_restaurants,
        "total_food_items": total_foods,
        "total_orders": len(all_orders),
        "today_orders": len(today_orders),
        "total_revenue": round(total_revenue, 2),
        "wallet_bonuses_paid": round(wallet_bonuses, 2),
        "active_users": active_users,
        "payment_stats": payment_stats,
    }), 200


# ---------------------------- Platform-wide analytics ----------------------------
@admin_bp.route("/analytics", methods=["GET"])
@token_required(["admin"])
def analytics():
    """
    Platform-wide analytics for the Admin Dashboard. Revenue is a single
    combined total across every restaurant (never broken out per restaurant),
    and customer growth counts every registered customer on the platform.
    Uses SQL-side aggregation (extract + group_by) instead of loading every
    row into memory.
    """
    from sqlalchemy import extract, func

    # ---- Customer growth by registration month (all customers, platform-wide) ----
    customer_rows = (
        db.session.query(
            extract("year", Customer.created_at).label("yr"),
            extract("month", Customer.created_at).label("mo"),
            func.count(Customer.id).label("cnt"),
        )
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .all()
    )
    customers_by_month = {(int(y), int(m)): int(c) for y, m, c in customer_rows}

    # ---- Total platform revenue by month (all restaurants combined, paid orders only) ----
    revenue_rows = (
        db.session.query(
            extract("year", Order.created_at).label("yr"),
            extract("month", Order.created_at).label("mo"),
            func.sum(Order.total_amount).label("total"),
        )
        .filter(Order.payment_status == "paid")
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .all()
    )
    revenue_by_month = {(int(y), int(m)): float(t or 0) for y, m, t in revenue_rows}

    all_keys = sorted(set(customers_by_month) | set(revenue_by_month))
    monthly_customers = [
        {"month": f"{MONTH_NAMES[m - 1]} {y}", "customers": customers_by_month.get((y, m), 0)}
        for (y, m) in all_keys
    ]
    monthly_revenue = [
        {"month": f"{MONTH_NAMES[m - 1]} {y}", "revenue": round(revenue_by_month.get((y, m), 0), 2)}
        for (y, m) in all_keys
    ]

    return jsonify({
        "monthly_customers": monthly_customers,
        "monthly_revenue": monthly_revenue,
    }), 200


# ---------------------------- Restaurant management ----------------------------
@admin_bp.route("/restaurants", methods=["GET"])
@token_required(["admin"])
def list_restaurants():
    q = Restaurant.query
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    search = request.args.get("search")
    if search:
        q = q.filter(Restaurant.restaurant_name.ilike(f"%{search}%"))
    restaurants = q.order_by(Restaurant.created_at.desc()).all()
    return jsonify([{
        "id": r.id, "restaurant_name": r.restaurant_name, "owner_name": r.owner_name,
        "email": r.user.email, "mobile_number": r.mobile_number, "status": r.status,
        "created_at": r.created_at.isoformat(), "rating": float(r.rating or 0),
    } for r in restaurants]), 200


@admin_bp.route("/restaurants/<int:restaurant_id>", methods=["GET"])
@token_required(["admin"])
def get_restaurant_detail(restaurant_id):
    r = Restaurant.query.get(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found."}), 404
    foods = Food.query.filter_by(restaurant_id=r.id).all()
    orders = Order.query.filter_by(restaurant_id=r.id).all()
    return jsonify({
        "id": r.id, "restaurant_name": r.restaurant_name, "owner_name": r.owner_name,
        "email": r.user.email, "mobile_number": r.mobile_number, "address": r.address,
        "status": r.status, "description": r.description, "created_at": r.created_at.isoformat(),
        "food_count": len(foods), "order_count": len(orders),
    }), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/approve", methods=["PUT"])
@token_required(["admin"])
def approve_restaurant(restaurant_id):
    r = Restaurant.query.get(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found."}), 404
    r.status = "approved"
    db.session.add(Notification(recipient_role="restaurant", recipient_id=r.id,
                                 title="Application Approved", message="Your restaurant has been approved. You can now log in."))
    db.session.commit()
    return jsonify({"message": "Restaurant approved.", "status": r.status}), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/reject", methods=["PUT"])
@token_required(["admin"])
def reject_restaurant(restaurant_id):
    r = Restaurant.query.get(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found."}), 404
    r.status = "rejected"
    db.session.add(Notification(recipient_role="restaurant", recipient_id=r.id,
                                 title="Application Rejected", message="Your restaurant application was rejected."))
    db.session.commit()
    return jsonify({"message": "Restaurant rejected.", "status": r.status}), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/status", methods=["PUT"])
@token_required(["admin"])
def set_restaurant_status(restaurant_id):
    data = request.get_json(force=True) or {}
    status = data.get("status")
    if status not in ("pending", "approved", "rejected", "deactivated"):
        return jsonify({"error": "Invalid status."}), 400
    r = Restaurant.query.get(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found."}), 404
    r.status = status
    db.session.commit()
    return jsonify({"message": "Status updated.", "status": r.status}), 200


@admin_bp.route("/restaurants/<int:restaurant_id>", methods=["DELETE"])
@token_required(["admin"])
def delete_restaurant(restaurant_id):
    r = Restaurant.query.get(restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found."}), 404
    db.session.delete(r.user)  # cascades to restaurant via FK
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "Restaurant deleted."}), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/foods", methods=["GET"])
@token_required(["admin"])
def restaurant_foods(restaurant_id):
    foods = Food.query.filter_by(restaurant_id=restaurant_id).all()
    return jsonify([serialize_food(f) for f in foods]), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/orders", methods=["GET"])
@token_required(["admin"])
def restaurant_orders_admin(restaurant_id):
    orders = Order.query.filter_by(restaurant_id=restaurant_id).order_by(Order.created_at.desc()).all()
    return jsonify([_serialize_order(o) for o in orders]), 200


# ---------------------------- Customer management ----------------------------
@admin_bp.route("/customers", methods=["GET"])
@token_required(["admin"])
def list_customers():
    q = Customer.query
    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        q = q.filter((Customer.first_name.ilike(like)) | (Customer.last_name.ilike(like)) | (Customer.mobile_number.ilike(like)))
    customers = q.order_by(Customer.created_at.desc()).all()
    return jsonify([{
        "id": c.id, "name": f"{c.first_name} {c.last_name}", "email": c.user.email,
        "mobile_number": c.mobile_number, "is_active": c.user.is_active,
        "created_at": c.created_at.isoformat(),
    } for c in customers]), 200


@admin_bp.route("/customers/<int:customer_id>", methods=["GET"])
@token_required(["admin"])
def customer_detail(customer_id):
    c = Customer.query.get(customer_id)
    if not c:
        return jsonify({"error": "Customer not found."}), 404
    orders = Order.query.filter_by(customer_id=c.id).order_by(Order.created_at.desc()).all()
    wallet = Wallet.query.filter_by(customer_id=c.id).first()
    game_sessions = GameSession.query.filter_by(customer_id=c.id, status="completed").count()
    # NOTE: password is never included -- passwords are hashed and never exposed.
    return jsonify({
        "id": c.id, "name": f"{c.first_name} {c.last_name}", "email": c.user.email,
        "mobile_number": c.mobile_number, "is_active": c.user.is_active,
        "order_count": len(orders),
        "wallet_balance": float(wallet.balance) if wallet else 0,
        "game_sessions_played": game_sessions,
        "orders": [_serialize_order(o) for o in orders[:20]],
    }), 200


@admin_bp.route("/customers/<int:customer_id>/status", methods=["PUT"])
@token_required(["admin"])
def set_customer_status(customer_id):
    data = request.get_json(force=True) or {}
    c = Customer.query.get(customer_id)
    if not c:
        return jsonify({"error": "Customer not found."}), 404
    c.user.is_active = bool(data.get("is_active", True))
    db.session.commit()
    return jsonify({"message": "Customer status updated.", "is_active": c.user.is_active}), 200


@admin_bp.route("/customers/<int:customer_id>/wallet-transactions", methods=["GET"])
@token_required(["admin"])
def customer_wallet_transactions(customer_id):
    wallet = Wallet.query.filter_by(customer_id=customer_id).first()
    if not wallet:
        return jsonify([]), 200
    txns = WalletTransaction.query.filter_by(wallet_id=wallet.id).order_by(WalletTransaction.created_at.desc()).all()
    return jsonify([{
        "id": t.id, "type": t.type, "amount": float(t.amount), "reason": t.reason,
        "balance_after": float(t.balance_after), "created_at": t.created_at.isoformat(),
    } for t in txns]), 200


# ---------------------------- Category management ----------------------------
@admin_bp.route("/categories", methods=["GET"])
@token_required(["admin"])
def list_all_categories():
    cats = Category.query.order_by(Category.name).all()
    return jsonify([{
        "id": c.id, "name": c.name, "image_url": c.image_url, "is_active": c.is_active,
        "food_count": Food.query.filter_by(category_id=c.id).count(),
    } for c in cats]), 200


@admin_bp.route("/categories", methods=["POST"])
@token_required(["admin"])
def add_category():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Category name is required."}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({"error": "Category already exists."}), 409
    cat = Category(name=name, image_url=data.get("image_url", ""), is_active=True)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"id": cat.id, "name": cat.name}), 201


@admin_bp.route("/categories/<int:category_id>", methods=["PUT"])
@token_required(["admin"])
def update_category(category_id):
    cat = Category.query.get(category_id)
    if not cat:
        return jsonify({"error": "Category not found."}), 404
    data = request.get_json(force=True) or {}
    if "name" in data:
        cat.name = data["name"]
    if "image_url" in data:
        cat.image_url = data["image_url"]
    if "is_active" in data:
        cat.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify({"message": "Category updated."}), 200


@admin_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@token_required(["admin"])
def delete_category(category_id):
    if Food.query.filter_by(category_id=category_id).first():
        return jsonify({"error": "Cannot delete a category that still has food items."}), 400
    cat = Category.query.get(category_id)
    if not cat:
        return jsonify({"error": "Category not found."}), 404
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Category deleted."}), 200


# ---------------------------- Food management (any restaurant) ----------------------------
@admin_bp.route("/foods", methods=["GET"])
@token_required(["admin"])
def list_all_foods():
    foods = Food.query.order_by(Food.created_at.desc()).limit(500).all()
    return jsonify([serialize_food(f) for f in foods]), 200


@admin_bp.route("/foods/<int:food_id>", methods=["PUT"])
@token_required(["admin"])
def admin_update_food(food_id):
    food = Food.query.get(food_id)
    if not food:
        return jsonify({"error": "Food not found."}), 404
    data = request.get_json(force=True) or {}
    for field in ["name", "description", "image_url"]:
        if field in data:
            setattr(food, field, data[field])
    if "category_id" in data:
        food.category_id = data["category_id"]
    if "is_veg" in data:
        food.is_veg = bool(data["is_veg"])
    if "price" in data:
        food.price = float(data["price"])
    if "discount_percent" in data:
        food.discount_percent = float(data["discount_percent"])
    if "is_available" in data:
        food.is_available = bool(data["is_available"])
    db.session.commit()
    return jsonify(serialize_food(food)), 200


@admin_bp.route("/foods/<int:food_id>", methods=["DELETE"])
@token_required(["admin"])
def admin_delete_food(food_id):
    food = Food.query.get(food_id)
    if not food:
        return jsonify({"error": "Food not found."}), 404
    db.session.delete(food)
    db.session.commit()
    return jsonify({"message": "Food deleted."}), 200


# ---------------------------- Order management ----------------------------
@admin_bp.route("/orders", methods=["GET"])
@token_required(["admin"])
def list_all_orders():
    q = Order.query
    payment_status = request.args.get("payment_status")
    order_status = request.args.get("order_status")
    if payment_status:
        q = q.filter_by(payment_status=payment_status)
    if order_status:
        q = q.filter_by(order_status=order_status)
    orders = q.order_by(Order.created_at.desc()).limit(500).all()
    return jsonify([_serialize_order(o) for o in orders]), 200


# ---------------------------- Payment management ----------------------------
@admin_bp.route("/payments", methods=["GET"])
@token_required(["admin"])
def list_payments():
    q = Payment.query
    method = request.args.get("method")
    status = request.args.get("status")
    if method:
        q = q.filter_by(method=method)
    if status:
        q = q.filter_by(status=status)
    payments = q.order_by(Payment.created_at.desc()).limit(500).all()
    return jsonify([{
        "id": p.id, "order_id": p.order_id, "method": p.method, "amount": float(p.amount),
        "status": p.status, "razorpay_payment_id": p.razorpay_payment_id,
        "created_at": p.created_at.isoformat(),
    } for p in payments]), 200


# ---------------------------- GK question bank management ----------------------------
@admin_bp.route("/game-questions", methods=["GET"])
@token_required(["admin"])
def list_questions():
    qs = GameQuestion.query.order_by(GameQuestion.id.desc()).all()
    return jsonify([{
        "id": q.id, "question": q.question,
        "option_a": q.option_a, "option_b": q.option_b, "option_c": q.option_c, "option_d": q.option_d,
        "correct_option": q.correct_option, "is_active": q.is_active,
    } for q in qs]), 200


@admin_bp.route("/game-questions", methods=["POST"])
@token_required(["admin"])
def add_question():
    data = request.get_json(force=True) or {}
    required = ["question", "option_a", "option_b", "option_c", "option_d", "correct_option"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if data["correct_option"] not in ("A", "B", "C", "D"):
        return jsonify({"error": "correct_option must be A, B, C, or D."}), 400

    q = GameQuestion(
        question=data["question"], option_a=data["option_a"], option_b=data["option_b"],
        option_c=data["option_c"], option_d=data["option_d"], correct_option=data["correct_option"],
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(q)
    db.session.commit()
    return jsonify({"id": q.id}), 201


@admin_bp.route("/game-questions/<int:question_id>", methods=["PUT"])
@token_required(["admin"])
def update_question(question_id):
    q = GameQuestion.query.get(question_id)
    if not q:
        return jsonify({"error": "Question not found."}), 404
    data = request.get_json(force=True) or {}
    for field in ["question", "option_a", "option_b", "option_c", "option_d", "correct_option"]:
        if field in data:
            setattr(q, field, data[field])
    if "is_active" in data:
        q.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify({"message": "Question updated."}), 200


@admin_bp.route("/game-questions/<int:question_id>", methods=["DELETE"])
@token_required(["admin"])
def delete_question(question_id):
    q = GameQuestion.query.get(question_id)
    if not q:
        return jsonify({"error": "Question not found."}), 404
    db.session.delete(q)
    db.session.commit()
    return jsonify({"message": "Question deleted."}), 200


@admin_bp.route("/game-stats", methods=["GET"])
@token_required(["admin"])
def game_stats():
    total_sessions = GameSession.query.filter_by(status="completed").count()
    total_rewards = db.session.query(db.func.coalesce(db.func.sum(GameSession.reward_amount), 0)) \
        .filter(GameSession.reward_claimed == True).scalar()  # noqa: E712
    avg_score = db.session.query(db.func.coalesce(db.func.avg(GameSession.score), 0)) \
        .filter_by(status="completed").scalar()
    return jsonify({
        "total_sessions_played": total_sessions,
        "total_rewards_paid": float(total_rewards or 0),
        "average_score": round(float(avg_score or 0), 2),
    }), 200
