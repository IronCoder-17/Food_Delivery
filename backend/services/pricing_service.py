"""
Single source of truth for "what does this food/combo actually cost right now".

Never trust a price sent by the frontend or cached on a cart row -- every
place that needs a price (cart display, checkout, reorder, meal planner)
must call through here so a restaurant's discount changes and time-boxed
Flash Sales are always reflected, and can never be spoofed by the client.
"""
from datetime import datetime

from backend.models.models import FlashSale
from backend.services import chef_special_service, surplus_service


def _active_flash_sale_for_food(food_id):
    now = datetime.utcnow()
    sales = FlashSale.query.filter(
        FlashSale.food_id == food_id,
        FlashSale.is_active.is_(True),
        FlashSale.start_time <= now,
        FlashSale.end_time >= now,
    ).all()
    live = [s for s in sales if s.is_currently_live()]
    if not live:
        return None
    # If multiple overlap (shouldn't normally happen), use the deepest discount.
    return max(live, key=lambda s: float(s.discount_percent))


def _active_flash_sale_for_combo(combo_id):
    now = datetime.utcnow()
    sales = FlashSale.query.filter(
        FlashSale.combo_id == combo_id,
        FlashSale.is_active.is_(True),
        FlashSale.start_time <= now,
        FlashSale.end_time >= now,
    ).all()
    live = [s for s in sales if s.is_currently_live()]
    if not live:
        return None
    return max(live, key=lambda s: float(s.discount_percent))


def effective_food_price(food):
    """Returns (price: float, flash_sale_info: dict|None).

    Priority when multiple deals could apply to the same food: a live Chef's
    Special (explicit, restaurant-committed price) > a live Surplus Deal
    (explicit surplus price) > a percent-off Flash Sale. All are mutually
    exclusive on purpose -- stacking would let a customer get a
    surplus-priced item further discounted by a flash sale, for example.
    Returned under the same 'flash_sale' key (with a 'source' field) so
    every existing caller (cart, checkout, reorder, group orders) picks up
    whichever deal applies with zero changes.
    """
    special = chef_special_service.active_special_for_food(food.id)
    if special:
        return float(special.special_price), {
            "flash_sale_id": None,
            "chef_special_id": special.id,
            "surplus_deal_id": None,
            "source": "chef_special",
            "discount_percent": None,
            "ends_at": special.end_time.isoformat(),
        }

    surplus = surplus_service.active_deal_for_food(food.id)
    if surplus:
        return float(surplus.discount_price), {
            "flash_sale_id": None,
            "chef_special_id": None,
            "surplus_deal_id": surplus.id,
            "source": "surplus_deal",
            "discount_percent": surplus.discount_percent,
            "ends_at": surplus.expiry_time.isoformat(),
        }

    base = food.final_price  # restaurant's own listed discount already applied
    sale = _active_flash_sale_for_food(food.id)
    if not sale:
        return base, None
    discounted = round(base - (base * float(sale.discount_percent) / 100), 2)
    return discounted, {
        "flash_sale_id": sale.id,
        "chef_special_id": None,
        "surplus_deal_id": None,
        "source": "flash_sale",
        "discount_percent": float(sale.discount_percent),
        "ends_at": sale.end_time.isoformat(),
    }


def effective_combo_price(combo):
    """Returns (price: float, flash_sale_info: dict|None)."""
    base = float(combo.combo_price)
    sale = _active_flash_sale_for_combo(combo.id)
    if not sale:
        return base, None
    discounted = round(base - (base * float(sale.discount_percent) / 100), 2)
    return discounted, {
        "flash_sale_id": sale.id,
        "discount_percent": float(sale.discount_percent),
        "ends_at": sale.end_time.isoformat(),
    }


def register_flash_sale_usage(flash_sale_id, quantity):
    """Called once an order is actually placed using this sale's discount."""
    if not flash_sale_id:
        return
    sale = FlashSale.query.get(flash_sale_id)
    if sale:
        sale.sold_quantity = (sale.sold_quantity or 0) + quantity


def register_deal_usage(flash_sale_info, quantity):
    """Given the flash_sale_info dict returned by effective_food_price/
    effective_combo_price, registers usage against whichever deal (Flash
    Sale, Chef's Special, or Surplus Deal) actually applied. Safe to call
    with None."""
    if not flash_sale_info:
        return
    if flash_sale_info.get("chef_special_id"):
        chef_special_service.register_usage(flash_sale_info["chef_special_id"], quantity)
    elif flash_sale_info.get("surplus_deal_id"):
        surplus_service.register_usage(flash_sale_info["surplus_deal_id"], quantity)
    elif flash_sale_info.get("flash_sale_id"):
        register_flash_sale_usage(flash_sale_info["flash_sale_id"], quantity)
