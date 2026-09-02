"""
Favorites / Wishlist -- customers can favorite Foods and Restaurants.
"""
from flask import Blueprint, jsonify, g

from backend.models.models import db, Customer, Food, Restaurant, FavoriteFood, FavoriteRestaurant
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.routes.food_routes import serialize_food, _serialize_time

favorite_bp = Blueprint("favorite", __name__, url_prefix="/api/customer/favorites")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


def _serialize_restaurant(r: Restaurant):
    return {
        "id": r.id, "name": r.restaurant_name, "description": r.description,
        "logo_url": r.logo_url, "cover_image_url": r.cover_image_url,
        "rating": float(r.rating or 0),
        "opening_time": _serialize_time(r.opening_time),
        "closing_time": _serialize_time(r.closing_time),
        "status": r.status,
    }


@favorite_bp.route("/foods", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.favorites")
def list_favorite_foods():
    customer = _get_own_customer()
    favs = FavoriteFood.query.filter_by(customer_id=customer.id) \
        .order_by(FavoriteFood.created_at.desc()).all()
    return jsonify([serialize_food(f.food) for f in favs if f.food]), 200


@favorite_bp.route("/foods/<int:food_id>", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.favorites")
def add_favorite_food(food_id):
    customer = _get_own_customer()
    food = Food.query.get(food_id)
    if not food:
        return jsonify({"error": "Food not found."}), 404

    existing = FavoriteFood.query.filter_by(customer_id=customer.id, food_id=food_id).first()
    if existing:
        return jsonify({"message": "Already in favorites."}), 200

    db.session.add(FavoriteFood(customer_id=customer.id, food_id=food_id))
    db.session.commit()
    return jsonify({"message": "Added to favorites."}), 201


@favorite_bp.route("/foods/<int:food_id>", methods=["DELETE"])
@token_required(["customer"])
@require_permission("customer.favorites")
def remove_favorite_food(food_id):
    customer = _get_own_customer()
    fav = FavoriteFood.query.filter_by(customer_id=customer.id, food_id=food_id).first()
    if not fav:
        return jsonify({"error": "Not in favorites."}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Removed from favorites."}), 200


@favorite_bp.route("/restaurants", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.favorites")
def list_favorite_restaurants():
    customer = _get_own_customer()
    favs = FavoriteRestaurant.query.filter_by(customer_id=customer.id) \
        .order_by(FavoriteRestaurant.created_at.desc()).all()
    return jsonify([_serialize_restaurant(f.restaurant) for f in favs if f.restaurant]), 200


@favorite_bp.route("/restaurants/<int:restaurant_id>", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.favorites")
def add_favorite_restaurant(restaurant_id):
    customer = _get_own_customer()
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found."}), 404

    existing = FavoriteRestaurant.query.filter_by(customer_id=customer.id, restaurant_id=restaurant_id).first()
    if existing:
        return jsonify({"message": "Already in favorites."}), 200

    db.session.add(FavoriteRestaurant(customer_id=customer.id, restaurant_id=restaurant_id))
    db.session.commit()
    return jsonify({"message": "Added to favorites."}), 201


@favorite_bp.route("/restaurants/<int:restaurant_id>", methods=["DELETE"])
@token_required(["customer"])
@require_permission("customer.favorites")
def remove_favorite_restaurant(restaurant_id):
    customer = _get_own_customer()
    fav = FavoriteRestaurant.query.filter_by(customer_id=customer.id, restaurant_id=restaurant_id).first()
    if not fav:
        return jsonify({"error": "Not in favorites."}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Removed from favorites."}), 200


@favorite_bp.route("/status", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.favorites")
def favorite_status():
    """Bulk-check which food/restaurant ids (from query params, comma-separated)
    are currently favorited, so list pages can render hearts without N+1 calls.
    e.g. /status?food_ids=1,2,3&restaurant_ids=4,5
    """
    from flask import request
    customer = _get_own_customer()

    food_ids_raw = request.args.get("food_ids", "")
    restaurant_ids_raw = request.args.get("restaurant_ids", "")
    food_ids = [int(x) for x in food_ids_raw.split(",") if x.strip().isdigit()]
    restaurant_ids = [int(x) for x in restaurant_ids_raw.split(",") if x.strip().isdigit()]

    fav_food_ids = set()
    if food_ids:
        fav_food_ids = {
            f.food_id for f in FavoriteFood.query.filter(
                FavoriteFood.customer_id == customer.id, FavoriteFood.food_id.in_(food_ids)
            ).all()
        }
    fav_restaurant_ids = set()
    if restaurant_ids:
        fav_restaurant_ids = {
            f.restaurant_id for f in FavoriteRestaurant.query.filter(
                FavoriteRestaurant.customer_id == customer.id, FavoriteRestaurant.restaurant_id.in_(restaurant_ids)
            ).all()
        }

    return jsonify({
        "foods": sorted(fav_food_ids),
        "restaurants": sorted(fav_restaurant_ids),
    }), 200