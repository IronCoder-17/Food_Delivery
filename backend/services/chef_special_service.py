"""
Chef's Specials. Modeled closely on the existing Flash Sale system
(backend/services/pricing_service.py + backend/routes/flash_sale_routes.py)
but kept as its own table: a Chef's Special has an explicit special_price,
a hard quantity cap, and its own description/image -- not a percent-off an
existing listing.

Server-enforced, first-come-first-served: quantity_sold only ever increments
at the moment an order is actually placed (see register_usage(), called from
order_routes.py), never from anything the frontend reports.
"""
from datetime import datetime

from backend.models.models import db, ChefSpecial


def active_special_for_food(food_id):
    """The currently-live Chef's Special for this food, if any. If more than
    one somehow overlaps, prefer the one ending soonest (most urgent)."""
    now = datetime.utcnow()
    candidates = ChefSpecial.query.filter(
        ChefSpecial.food_id == food_id,
        ChefSpecial.is_active.is_(True),
        ChefSpecial.start_time <= now,
        ChefSpecial.end_time >= now,
    ).all()
    live = [c for c in candidates if c.is_currently_live()]
    if not live:
        return None
    return min(live, key=lambda c: c.end_time)


def register_usage(chef_special_id, quantity):
    """Called once an order is actually placed using this special's price."""
    if not chef_special_id:
        return
    special = ChefSpecial.query.get(chef_special_id)
    if special:
        special.quantity_sold = (special.quantity_sold or 0) + quantity


def serialize(s: ChefSpecial, include_restaurant=True):
    data = {
        "id": s.id,
        "food_id": s.food_id,
        "food_name": s.food.name if s.food else None,
        "food_image_url": s.image_url or (s.food.image_url if s.food else None),
        "special_price": float(s.special_price),
        "original_price": float(s.food.final_price) if s.food else None,
        "quantity_total": s.quantity_total,
        "quantity_sold": s.quantity_sold,
        "remaining_quantity": s.remaining_quantity,
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat(),
        "description": s.description,
        "is_active": bool(s.is_active),
        "is_currently_live": s.is_currently_live(),
    }
    if include_restaurant:
        data["restaurant_id"] = s.restaurant_id
        data["restaurant_name"] = s.restaurant.restaurant_name if s.restaurant else None
    return data
