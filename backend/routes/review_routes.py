"""
Reviews & Ratings.

Rules enforced server-side (never trust the frontend):
  * Only a customer who has a DELIVERED order containing that exact food
    item may review it.
  * One review per customer/order/food (DB unique constraint backs this up).
  * Food.rating / Restaurant.rating are always recomputed server-side.
"""
from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Customer, Restaurant, Food, Order, OrderItem, Review, ReviewReply
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.review_service import recalculate_all_for_review

review_bp = Blueprint("review", __name__, url_prefix="/api/customer/reviews")
restaurant_review_bp = Blueprint("restaurant_review", __name__, url_prefix="/api/restaurant/reviews")
public_review_bp = Blueprint("public_review", __name__, url_prefix="/api/foods")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


def _get_own_restaurant():
    return Restaurant.query.filter_by(user_id=g.user_id).first()


def _serialize_review(r: Review, include_customer_name=True):
    return {
        "id": r.id,
        "customer_id": r.customer_id,
        "customer_name": (f"{r.customer.first_name} {r.customer.last_name[0]}." if r.customer else None)
        if include_customer_name else None,
        "restaurant_id": r.restaurant_id,
        "food_id": r.food_id,
        "food_name": r.food.name if r.food else None,
        "order_id": r.order_id,
        "rating": r.rating,
        "comment": r.comment,
        "image_url": r.image_url,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "reply": {
            "reply_text": r.reply.reply_text,
            "created_at": r.reply.created_at.isoformat() if r.reply.created_at else None,
        } if r.reply else None,
    }


# ---------------------------------------------------------------------------
# Public: view reviews for a food (used on the food detail card)
# ---------------------------------------------------------------------------
@public_review_bp.route("/<int:food_id>/reviews", methods=["GET"])
def public_food_reviews(food_id):
    food = Food.query.get(food_id)
    if not food:
        return jsonify({"error": "Food not found."}), 404
    reviews = Review.query.filter_by(food_id=food_id, status="active") \
        .order_by(Review.created_at.desc()).limit(100).all()
    return jsonify([_serialize_review(r) for r in reviews]), 200


# ---------------------------------------------------------------------------
# Customer: create / list-mine / update / delete
# ---------------------------------------------------------------------------
@review_bp.route("", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.reviews")
def create_review():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}

    order_id = data.get("order_id")
    food_id = data.get("food_id")
    rating = data.get("rating")
    comment = (data.get("comment") or "").strip() or None
    image_url = (data.get("image_url") or "").strip() or None

    if not order_id or not food_id:
        return jsonify({"error": "order_id and food_id are required."}), 400
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "Rating must be an integer between 1 and 5."}), 400
    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5."}), 400

    order = Order.query.get(order_id)
    if not order or order.customer_id != customer.id:
        return jsonify({"error": "Order not found."}), 404
    if order.order_status != "delivered":
        return jsonify({"error": "You can only review items from a delivered order."}), 400

    item = OrderItem.query.filter_by(order_id=order.id, food_id=food_id).first()
    if not item:
        return jsonify({"error": "This food item was not part of that order."}), 400

    if Review.query.filter_by(customer_id=customer.id, order_id=order.id, food_id=food_id).first():
        return jsonify({"error": "You have already reviewed this item for this order."}), 409

    review = Review(
        customer_id=customer.id,
        restaurant_id=order.restaurant_id,
        food_id=food_id,
        order_id=order.id,
        rating=rating,
        comment=comment,
        image_url=image_url,
        status="active",
    )
    db.session.add(review)
    db.session.commit()

    recalculate_all_for_review(review)

    return jsonify(_serialize_review(review)), 201


@review_bp.route("/mine", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.reviews")
def my_reviews():
    customer = _get_own_customer()
    reviews = Review.query.filter_by(customer_id=customer.id).order_by(Review.created_at.desc()).all()
    return jsonify([_serialize_review(r) for r in reviews]), 200


@review_bp.route("/reviewable", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.reviews")
def reviewable_items():
    """Delivered order items the customer hasn't reviewed yet -- drives the
    'Write a Review' prompt on the Orders page."""
    customer = _get_own_customer()
    delivered_orders = Order.query.filter_by(customer_id=customer.id, order_status="delivered").all()
    already_reviewed = {
        (r.order_id, r.food_id) for r in Review.query.filter_by(customer_id=customer.id).all()
    }

    result = []
    for order in delivered_orders:
        for item in order.items:
            if (order.id, item.food_id) in already_reviewed:
                continue
            result.append({
                "order_id": order.id,
                "food_id": item.food_id,
                "food_name": item.food_name,
                "restaurant_name": order.restaurant.restaurant_name if order.restaurant else None,
                "delivered_at": order.updated_at.isoformat() if order.updated_at else None,
            })
    return jsonify(result), 200


@review_bp.route("/<int:review_id>", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.reviews")
def update_review(review_id):
    customer = _get_own_customer()
    review = Review.query.filter_by(id=review_id, customer_id=customer.id).first()
    if not review:
        return jsonify({"error": "Review not found."}), 404

    data = request.get_json(force=True) or {}
    if "rating" in data:
        try:
            rating = int(data["rating"])
        except (TypeError, ValueError):
            return jsonify({"error": "Rating must be an integer between 1 and 5."}), 400
        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5."}), 400
        review.rating = rating
    if "comment" in data:
        review.comment = (data.get("comment") or "").strip() or None
    if "image_url" in data:
        review.image_url = (data.get("image_url") or "").strip() or None

    db.session.commit()
    recalculate_all_for_review(review)
    return jsonify(_serialize_review(review)), 200


@review_bp.route("/<int:review_id>", methods=["DELETE"])
@token_required(["customer"])
@require_permission("customer.reviews")
def delete_review(review_id):
    customer = _get_own_customer()
    review = Review.query.filter_by(id=review_id, customer_id=customer.id).first()
    if not review:
        return jsonify({"error": "Review not found."}), 404

    food_id, restaurant_id = review.food_id, review.restaurant_id
    db.session.delete(review)
    db.session.commit()

    from backend.services.review_service import recalculate_food_rating, recalculate_restaurant_rating
    recalculate_food_rating(food_id)
    recalculate_restaurant_rating(restaurant_id)

    return jsonify({"message": "Review deleted."}), 200


# ---------------------------------------------------------------------------
# Restaurant: reply to a review on one of its own foods
# ---------------------------------------------------------------------------
@restaurant_review_bp.route("", methods=["GET"])
@token_required(["restaurant"])
def restaurant_list_reviews():
    restaurant = _get_own_restaurant()
    reviews = Review.query.filter_by(restaurant_id=restaurant.id, status="active") \
        .order_by(Review.created_at.desc()).all()
    return jsonify([_serialize_review(r) for r in reviews]), 200


@restaurant_review_bp.route("/<int:review_id>/reply", methods=["POST"])
@token_required(["restaurant"])
@require_permission("restaurant.reply_reviews")
def reply_to_review(review_id):
    restaurant = _get_own_restaurant()
    review = Review.query.filter_by(id=review_id, restaurant_id=restaurant.id).first()
    if not review:
        return jsonify({"error": "Review not found."}), 404

    data = request.get_json(force=True) or {}
    reply_text = (data.get("reply_text") or "").strip()
    if not reply_text:
        return jsonify({"error": "Reply text is required."}), 400

    if review.reply:
        review.reply.reply_text = reply_text
    else:
        db.session.add(ReviewReply(review_id=review.id, restaurant_id=restaurant.id, reply_text=reply_text))
    db.session.commit()

    return jsonify(_serialize_review(review)), 200


# ---------------------------------------------------------------------------
# Admin: moderation (hide/restore a review, e.g. abusive content)
# ---------------------------------------------------------------------------
admin_review_bp = Blueprint("admin_review", __name__, url_prefix="/api/admin/reviews")


@admin_review_bp.route("", methods=["GET"])
@token_required(["admin"])
def admin_list_reviews():
    status = request.args.get("status")
    q = Review.query
    if status:
        q = q.filter_by(status=status)
    reviews = q.order_by(Review.created_at.desc()).limit(500).all()
    return jsonify([_serialize_review(r) for r in reviews]), 200


@admin_review_bp.route("/<int:review_id>/status", methods=["PUT"])
@token_required(["admin"])
def admin_set_review_status(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found."}), 404

    data = request.get_json(force=True) or {}
    new_status = data.get("status")
    if new_status not in ("active", "hidden"):
        return jsonify({"error": "Status must be 'active' or 'hidden'."}), 400

    review.status = new_status
    db.session.commit()
    recalculate_all_for_review(review)
    return jsonify(_serialize_review(review)), 200
