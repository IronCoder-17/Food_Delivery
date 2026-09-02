from datetime import timedelta, time as time_type

from flask import Blueprint, request, jsonify, g
from backend.models.models import db, Restaurant, Food, Category, Order, OrderItem
from backend.middleware.auth_middleware import token_required
from backend.routes.food_routes import serialize_food
from backend.utils.validators import is_valid_mobile, is_valid_pincode
from backend.services.authority_service import require_permission, has_permission
from backend.services import food_tags_service, kitchen_service

restaurant_bp = Blueprint("restaurant", __name__, url_prefix="/api/restaurant")

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


def _format_time(value):
    """
    MySQL TIME columns come back from PyMySQL as datetime.timedelta (not str),
    while SQLite/other setups may already hand back a plain string or a
    datetime.time. Normalize all of these to a "HH:MM" string so the value is
    always JSON-serializable and consistent for the frontend <input type="time">.
    """
    if value is None:
        return None
    if isinstance(value, timedelta):
        total_minutes = int(value.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        hours %= 24
        return f"{hours:02d}:{minutes:02d}"
    if isinstance(value, time_type):
        return value.strftime("%H:%M")
    return str(value)[:5]


def _serialize_restaurant_profile(r):
    return {
        "id": r.id, "restaurant_name": r.restaurant_name, "owner_name": r.owner_name,
        "email": r.user.email, "mobile_number": r.mobile_number, "address": r.address,
        "state_id": r.state_id, "city_id": r.city_id, "pincode": r.pincode,
        "description": r.description, "logo_url": r.logo_url, "cover_image_url": r.cover_image_url,
        "opening_time": _format_time(r.opening_time), "closing_time": _format_time(r.closing_time),
        "status": r.status, "rating": float(r.rating or 0),
    }


@restaurant_bp.route("/profile", methods=["GET"])
@token_required(["restaurant"])
@require_permission("restaurant.view_profile")
def get_profile():
    r = _get_own_restaurant()
    if not r:
        return jsonify({"error": "Restaurant profile not found."}), 404
    return jsonify(_serialize_restaurant_profile(r)), 200


@restaurant_bp.route("/profile", methods=["PUT"])
@token_required(["restaurant"])
@require_permission("restaurant.edit_profile")
def update_profile():
    r = _get_own_restaurant()
    if not r:
        return jsonify({"error": "Restaurant profile not found."}), 404

    data = request.get_json(force=True) or {}

    if "restaurant_name" in data:
        name = (data["restaurant_name"] or "").strip()
        if not name:
            return jsonify({"error": "Restaurant name cannot be empty."}), 400
        r.restaurant_name = name

    if "owner_name" in data:
        owner_name = (data["owner_name"] or "").strip()
        if not owner_name:
            return jsonify({"error": "Owner name cannot be empty."}), 400
        r.owner_name = owner_name

    if "mobile_number" in data and data["mobile_number"]:
        mobile = str(data["mobile_number"]).strip()
        if not is_valid_mobile(mobile):
            return jsonify({"error": "Invalid mobile number."}), 400
        if mobile != r.mobile_number and Restaurant.query.filter_by(mobile_number=mobile).first():
            return jsonify({"error": "Mobile number already in use."}), 409
        r.mobile_number = mobile

    if "pincode" in data and data["pincode"]:
        pincode = str(data["pincode"]).strip()
        if not is_valid_pincode(pincode):
            return jsonify({"error": "Invalid pincode."}), 400
        r.pincode = pincode

    for field in ["address", "description", "logo_url", "cover_image_url", "opening_time", "closing_time"]:
        if field in data:
            setattr(r, field, data[field])

    if "state_id" in data:
        r.state_id = data["state_id"] or None
    if "city_id" in data:
        r.city_id = data["city_id"] or None

    # Deliberately not settable from this endpoint: status, restaurant id, user role.
    db.session.commit()
    return jsonify({"message": "Profile updated successfully.", "restaurant": _serialize_restaurant_profile(r)}), 200


@restaurant_bp.route("/dashboard", methods=["GET"])
@token_required(["restaurant"])
@require_permission("restaurant.dashboard")
def dashboard():
    r = _get_own_restaurant()
    if not r:
        return jsonify({"error": "Restaurant profile not found."}), 404
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    all_orders = Order.query.filter_by(restaurant_id=r.id).all()
    today_orders = [o for o in all_orders if o.created_at >= today_start]
    pending = [o for o in all_orders if o.order_status in ("placed", "accepted", "preparing", "ready", "out_for_delivery")]
    completed = [o for o in all_orders if o.order_status == "delivered"]
    total_foods = Food.query.filter_by(restaurant_id=r.id).count()
    available_foods = Food.query.filter_by(restaurant_id=r.id, is_available=True).count()
    revenue = sum(float(o.total_amount) for o in completed)

    return jsonify({
        "total_orders": len(all_orders),
        "today_orders": len(today_orders),
        "pending_orders": len(pending),
        "completed_orders": len(completed),
        "total_food_items": total_foods,
        "available_food_items": available_foods,
        "total_revenue": round(revenue, 2),
    }), 200


# ---------------------- Analytics (own restaurant only) ----------------------
@restaurant_bp.route("/analytics", methods=["GET"])
@token_required(["restaurant"])
@require_permission("restaurant.analytics")
def analytics():
    """
    Returns chart-ready analytics scoped strictly to the currently
    authenticated restaurant (resolved from g.user_id via _get_own_restaurant()).
    No other restaurant's data is ever queried or returned.
    """
    r = _get_own_restaurant()
    if not r:
        return jsonify({"error": "Restaurant profile not found."}), 404

    # ---- Monthly revenue: uses the same "delivered" definition as /dashboard ----
    revenue_by_month = {}
    delivered_orders = Order.query.filter_by(restaurant_id=r.id, order_status="delivered").all()
    for o in delivered_orders:
        key = (o.created_at.year, o.created_at.month)
        revenue_by_month[key] = revenue_by_month.get(key, 0) + float(o.total_amount)

    # ---- Monthly unique customers & order counts: based on all orders placed ----
    customers_by_month = {}
    orders_count_by_month = {}
    all_orders = Order.query.filter_by(restaurant_id=r.id).all()
    for o in all_orders:
        key = (o.created_at.year, o.created_at.month)
        customers_by_month.setdefault(key, set()).add(o.customer_id)
        orders_count_by_month[key] = orders_count_by_month.get(key, 0) + 1

    all_keys = sorted(set(revenue_by_month) | set(customers_by_month))
    monthly_revenue = [
        {"month": f"{MONTH_NAMES[m - 1]} {y}", "revenue": round(revenue_by_month.get((y, m), 0), 2)}
        for (y, m) in all_keys
    ]
    monthly_customers = [
        {
            "month": f"{MONTH_NAMES[m - 1]} {y}",
            "customers": len(customers_by_month.get((y, m), set())),
            "orders": orders_count_by_month.get((y, m), 0),
        }
        for (y, m) in all_keys
    ]

    # ---- Most ordered food categories (this restaurant's foods only) ----
    category_totals = {}
    rows = (
        db.session.query(Category.name, OrderItem.quantity)
        .join(Order, OrderItem.order_id == Order.id)
        .join(Food, OrderItem.food_id == Food.id)
        .join(Category, Food.category_id == Category.id)
        .filter(Order.restaurant_id == r.id)
        .all()
    )
    for category_name, quantity in rows:
        category_totals[category_name] = category_totals.get(category_name, 0) + int(quantity or 0)

    food_categories = [
        {"category": name, "orders": qty}
        for name, qty in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return jsonify({
        "monthly_revenue": monthly_revenue,
        "monthly_customers": monthly_customers,
        "food_categories": food_categories,
    }), 200


# ---------------------- Food management (own foods only) ----------------------
@restaurant_bp.route("/foods", methods=["GET"])
@token_required(["restaurant"])
def list_own_foods():
    r = _get_own_restaurant()
    foods = Food.query.filter_by(restaurant_id=r.id).order_by(Food.created_at.desc()).all()
    return jsonify([serialize_food(f) for f in foods]), 200


def _require_food_permission(restaurant_id, specific_key):
    """Food management is gated by TWO permissions: the 'manage_food'
    master switch (disables all food actions at once) AND the specific
    action's own permission (add/edit/delete). Both must be allowed."""
    if not has_permission(restaurant_id, "restaurant", "restaurant.manage_food"):
        return "Food management has been restricted by the administrator."
    if not has_permission(restaurant_id, "restaurant", specific_key):
        return "This specific food action has been restricted by the administrator."
    return None


@restaurant_bp.route("/foods", methods=["POST"])
@token_required(["restaurant"])
def add_food():
    r = _get_own_restaurant()
    denial = _require_food_permission(r.id, "restaurant.add_food")
    if denial:
        return jsonify({"error": denial}), 403

    data = request.get_json(force=True) or {}
    required = ["name", "category_id", "price"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    if not Category.query.get(data["category_id"]):
        return jsonify({"error": "Invalid category."}), 400

    food = Food(
        restaurant_id=r.id,
        category_id=data["category_id"],
        name=data["name"],
        is_veg=bool(data.get("is_veg", True)),
        description=data.get("description", ""),
        price=float(data["price"]),
        discount_percent=float(data.get("discount_percent", 0)),
        image_url=data.get("image_url", ""),
        preparation_time_minutes=int(data.get("preparation_time_minutes", 20)),
        is_available=bool(data.get("is_available", True)),
        calories=data.get("calories") or None,
        protein_grams=data.get("protein_grams") or None,
        carbs_grams=data.get("carbs_grams") or None,
        fat_grams=data.get("fat_grams") or None,
    )
    db.session.add(food)
    db.session.flush()
    if "mood_ids" in data and has_permission(r.id, "restaurant", "restaurant.manage_food_tags"):
        food_tags_service.set_food_moods(food.id, data.get("mood_ids"))
    if "allergen_ids" in data and has_permission(r.id, "restaurant", "restaurant.manage_food_tags"):
        food_tags_service.set_food_allergens(food.id, data.get("allergen_ids"))
    db.session.commit()
    return jsonify(serialize_food(food)), 201


def _own_food_or_404(food_id):
    r = _get_own_restaurant()
    food = Food.query.filter_by(id=food_id, restaurant_id=r.id).first()
    return food


@restaurant_bp.route("/foods/<int:food_id>/inventory", methods=["PUT"])
@token_required(["restaurant"])
@require_permission("restaurant.manage_inventory")
def update_food_inventory(food_id):
    """Inventory-aware sold-out management. When track_inventory is on,
    is_available is always derived server-side from stock_quantity -- a
    restaurant can't leave stock at 0 while flagging the item available."""
    r = _get_own_restaurant()
    food = _own_food_or_404(food_id)
    if not food:
        return jsonify({"error": "Food not found or you don't own this item."}), 404

    data = request.get_json(force=True) or {}

    if "track_inventory" in data:
        food.track_inventory = bool(data["track_inventory"])

    if "stock_quantity" in data and data["stock_quantity"] is not None:
        try:
            qty = int(data["stock_quantity"])
            if qty < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "stock_quantity must be a non-negative integer."}), 400
        food.stock_quantity = qty

    if "low_stock_threshold" in data:
        try:
            threshold = int(data["low_stock_threshold"])
            if threshold < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "low_stock_threshold must be a non-negative integer."}), 400
        food.low_stock_threshold = threshold

    # Sold-out auto-management: while inventory tracking is on, availability
    # always follows stock, overriding whatever is_available was set to
    # before -- this is what makes "Stock = 0 -> Sold Out" automatic.
    if food.track_inventory:
        food.is_available = (food.stock_quantity or 0) > 0

    db.session.commit()
    return jsonify(serialize_food(food)), 200


@restaurant_bp.route("/foods/<int:food_id>", methods=["PUT"])
@token_required(["restaurant"])
def update_food(food_id):
    r = _get_own_restaurant()
    denial = _require_food_permission(r.id, "restaurant.edit_food")
    if denial:
        return jsonify({"error": denial}), 403

    food = _own_food_or_404(food_id)
    if not food:
        return jsonify({"error": "Food not found or you don't own this item."}), 404

    data = request.get_json(force=True) or {}
    if "price" in data and not has_permission(r.id, "restaurant", "restaurant.set_price"):
        return jsonify({"error": "Changing price has been restricted by the administrator."}), 403
    if "is_veg" in data and not has_permission(r.id, "restaurant", "restaurant.set_veg_nonveg"):
        return jsonify({"error": "Changing veg/non-veg status has been restricted by the administrator."}), 403
    if "category_id" in data and not has_permission(r.id, "restaurant", "restaurant.manage_categories"):
        return jsonify({"error": "Changing category has been restricted by the administrator."}), 403
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
    if "preparation_time_minutes" in data:
        food.preparation_time_minutes = int(data["preparation_time_minutes"])
    if "is_available" in data:
        if food.track_inventory and bool(data["is_available"]) and (food.stock_quantity or 0) <= 0:
            return jsonify({"error": "Cannot mark available: stock is 0. Update inventory stock instead."}), 400
        food.is_available = bool(data["is_available"])

    if any(k in data for k in ("calories", "protein_grams", "carbs_grams", "fat_grams")):
        if not has_permission(r.id, "restaurant", "restaurant.manage_nutrition_info"):
            return jsonify({"error": "Managing nutrition info has been restricted by the administrator."}), 403
        if "calories" in data:
            food.calories = data["calories"] or None
        if "protein_grams" in data:
            food.protein_grams = data["protein_grams"] or None
        if "carbs_grams" in data:
            food.carbs_grams = data["carbs_grams"] or None
        if "fat_grams" in data:
            food.fat_grams = data["fat_grams"] or None

    if "mood_ids" in data:
        if not has_permission(r.id, "restaurant", "restaurant.manage_food_tags"):
            return jsonify({"error": "Managing food tags has been restricted by the administrator."}), 403
        food_tags_service.set_food_moods(food.id, data.get("mood_ids"))
    if "allergen_ids" in data:
        if not has_permission(r.id, "restaurant", "restaurant.manage_food_tags"):
            return jsonify({"error": "Managing food tags has been restricted by the administrator."}), 403
        food_tags_service.set_food_allergens(food.id, data.get("allergen_ids"))

    db.session.commit()
    return jsonify(serialize_food(food)), 200


@restaurant_bp.route("/foods/<int:food_id>", methods=["DELETE"])
@token_required(["restaurant"])
def delete_food(food_id):
    r = _get_own_restaurant()
    denial = _require_food_permission(r.id, "restaurant.delete_food")
    if denial:
        return jsonify({"error": denial}), 403

    food = _own_food_or_404(food_id)
    if not food:
        return jsonify({"error": "Food not found or you don't own this item."}), 404
    db.session.delete(food)
    db.session.commit()
    return jsonify({"message": "Food deleted."}), 200