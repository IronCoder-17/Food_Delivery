from datetime import time, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from backend.models.models import db, Food, Category, Restaurant, FoodMoodMapping, FoodAllergenMapping
from backend.services.pricing_service import effective_food_price
from backend.services import food_tags_service, kitchen_service

food_bp = Blueprint("food", __name__, url_prefix="/api/foods")


def serialize_food(f: Food):
    effective_price, flash_sale = effective_food_price(f)
    return {
        "id": f.id,
        "name": f.name,
        "category_id": f.category_id,
        "category": f.category.name if f.category else None,
        "is_veg": bool(f.is_veg),
        "description": f.description,
        "price": float(f.price),
        "discount_percent": float(f.discount_percent or 0),
        "final_price": f.final_price,
        "effective_price": effective_price,
        "flash_sale": flash_sale,
        "image_url": f.image_url,
        "restaurant_id": f.restaurant_id,
        "restaurant_name": f.restaurant.restaurant_name if f.restaurant else None,
        "is_available": bool(f.is_available),
        "track_inventory": bool(f.track_inventory),
        "stock_quantity": f.stock_quantity if f.track_inventory else None,
        "is_low_stock": f.is_low_stock,
        "preparation_time_minutes": f.preparation_time_minutes,
        "rating": float(f.rating or 0),
        "moods": [{"id": m.id, "name": m.name, "emoji": m.emoji} for m in food_tags_service.get_food_moods(f.id)],
        "allergens": [{"id": a.id, "name": a.name} for a in food_tags_service.get_food_allergens(f.id)],
        "kitchen_status": kitchen_service.get_or_default(f.restaurant_id),
        "calories": f.calories,
        "protein_grams": float(f.protein_grams) if f.protein_grams is not None else None,
        "carbs_grams": float(f.carbs_grams) if f.carbs_grams is not None else None,
        "fat_grams": float(f.fat_grams) if f.fat_grams is not None else None,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }


@food_bp.route("/categories", methods=["GET"])
def list_categories():
    cats = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return jsonify([{"id": c.id, "name": c.name, "image_url": c.image_url} for c in cats]), 200


@food_bp.route("", methods=["GET"])
def list_foods():
    q = Food.query.join(Restaurant).filter(Restaurant.status == "approved")

    # By default, sold-out items stay hidden (original behavior). Pass
    # include_unavailable=true (used by the food listing page) to show them
    # with a "Sold Out" badge instead of silently disappearing.
    if request.args.get("include_unavailable") != "true":
        q = q.filter(Food.is_available == True)  # noqa: E712

    category_id = request.args.get("category_id", type=int)
    if category_id:
        q = q.filter(Food.category_id == category_id)

    veg = request.args.get("veg")
    if veg == "true":
        q = q.filter(Food.is_veg == True)  # noqa: E712
    elif veg == "false":
        q = q.filter(Food.is_veg == False)  # noqa: E712

    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Food.name.ilike(like), Food.description.ilike(like)))

    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    if min_price is not None:
        q = q.filter(Food.price >= min_price)
    if max_price is not None:
        q = q.filter(Food.price <= max_price)

    restaurant_id = request.args.get("restaurant_id", type=int)
    if restaurant_id:
        q = q.filter(Food.restaurant_id == restaurant_id)

    mood_id = request.args.get("mood_id", type=int)
    if mood_id:
        q = q.join(FoodMoodMapping, FoodMoodMapping.food_id == Food.id).filter(FoodMoodMapping.mood_id == mood_id)

    allergen_id = request.args.get("allergen_id", type=int)
    if allergen_id:
        q = q.join(FoodAllergenMapping, FoodAllergenMapping.food_id == Food.id).filter(FoodAllergenMapping.allergen_id == allergen_id)

    sort = request.args.get("sort")
    if sort == "price_low":
        q = q.order_by(Food.price.asc())
    elif sort == "price_high":
        q = q.order_by(Food.price.desc())
    elif sort == "rating":
        q = q.order_by(Food.rating.desc())
    else:
        q = q.order_by(Food.created_at.desc())

    foods = q.limit(200).all()
    return jsonify([serialize_food(f) for f in foods]), 200


@food_bp.route("/<int:food_id>", methods=["GET"])
def get_food(food_id):
    f = Food.query.get(food_id)
    if not f:
        return jsonify({"error": "Food not found."}), 404
    return jsonify(serialize_food(f)), 200


def _serialize_time(value):
    """Format a time-like value as HH:MM:SS text for JSON.

    The Restaurant model declares opening_time/closing_time as String, but
    when the underlying MySQL column is actually TIME, PyMySQL returns
    datetime.timedelta objects for those values instead of strings (and
    datetime.time in other drivers/configs). Normalize any of str / time /
    timedelta / None into a plain string so jsonify never chokes on it.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    return str(value)


@food_bp.route("/restaurants", methods=["GET"])
def list_restaurants():
    q = Restaurant.query.filter_by(status="approved")
    search = request.args.get("search")
    if search:
        q = q.filter(Restaurant.restaurant_name.ilike(f"%{search}%"))
    city_id = request.args.get("city_id", type=int)
    if city_id:
        q = q.filter(Restaurant.city_id == city_id)
    restaurants = q.all()
    return jsonify([{
        "id": r.id, "name": r.restaurant_name, "description": r.description,
        "logo_url": r.logo_url, "cover_image_url": r.cover_image_url,
        "rating": float(r.rating or 0),
        "opening_time": _serialize_time(r.opening_time),
        "closing_time": _serialize_time(r.closing_time),
        "kitchen_status": kitchen_service.get_or_default(r.id),
    } for r in restaurants]), 200