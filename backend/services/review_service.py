"""
Backend-controlled rating recalculation. Food.rating and Restaurant.rating
are NEVER set directly by any route -- they are always derived here from the
current set of active (non-moderated-hidden) reviews, so they can't drift or
be spoofed by client-supplied values.
"""
from backend.models.models import db, Food, Restaurant, Review


def recalculate_food_rating(food_id: int):
    food = Food.query.get(food_id)
    if not food:
        return
    reviews = Review.query.filter_by(food_id=food_id, status="active").all()
    if reviews:
        food.rating = round(sum(r.rating for r in reviews) / len(reviews), 2)
    else:
        food.rating = 0
    db.session.commit()


def recalculate_restaurant_rating(restaurant_id: int):
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return
    reviews = Review.query.filter_by(restaurant_id=restaurant_id, status="active").all()
    if reviews:
        restaurant.rating = round(sum(r.rating for r in reviews) / len(reviews), 2)
    else:
        restaurant.rating = 0
    db.session.commit()


def recalculate_all_for_review(review: Review):
    recalculate_food_rating(review.food_id)
    recalculate_restaurant_rating(review.restaurant_id)
