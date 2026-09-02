"""
Leftover / Surplus Food Deals. Restaurant lists near-expiry/surplus food at
a discount with a hard quantity cap and order deadline. The restaurant
remains solely responsible for food safety -- this system tracks price,
quantity, and timing only, and never certifies safety based on the timer.
"""
from datetime import datetime

from backend.models.models import db, SurplusDeal

SAFETY_DISCLAIMER = (
    "Surplus/leftover deals are provided by the restaurant. The restaurant "
    "is responsible for the safety and freshness of this food -- the order "
    "deadline and expiry time shown are restaurant-provided, not a safety "
    "guarantee from this platform."
)


def serialize(d: SurplusDeal, include_restaurant=True):
    data = {
        "id": d.id,
        "food_id": d.food_id,
        "food_name": d.food.name if d.food else None,
        "food_image_url": d.food.image_url if d.food else None,
        "original_price": float(d.original_price),
        "discount_price": float(d.discount_price),
        "discount_percent": d.discount_percent,
        "quantity_total": d.quantity_total,
        "quantity_sold": d.quantity_sold,
        "remaining_quantity": d.remaining_quantity,
        "order_deadline": d.order_deadline.isoformat(),
        "expiry_time": d.expiry_time.isoformat(),
        "is_active": bool(d.is_active),
        "is_currently_available": d.is_currently_available(),
        "safety_disclaimer": SAFETY_DISCLAIMER,
    }
    if include_restaurant:
        data["restaurant_id"] = d.restaurant_id
        data["restaurant_name"] = d.restaurant.restaurant_name if d.restaurant else None
    return data


def active_deal_for_food(food_id):
    """The currently-available surplus deal for this food, if any."""
    now = datetime.utcnow()
    candidates = SurplusDeal.query.filter(
        SurplusDeal.food_id == food_id,
        SurplusDeal.is_active.is_(True),
        SurplusDeal.order_deadline >= now,
        SurplusDeal.expiry_time >= now,
    ).all()
    available = [d for d in candidates if d.is_currently_available()]
    if not available:
        return None
    return min(available, key=lambda d: d.order_deadline)


def register_usage(surplus_deal_id, quantity):
    if not surplus_deal_id:
        return
    deal = SurplusDeal.query.get(surplus_deal_id)
    if deal:
        deal.quantity_sold = (deal.quantity_sold or 0) + quantity
