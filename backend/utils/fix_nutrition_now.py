"""
One-off fix-it script -- run this once to immediately fix Nutrition
Tracking on an existing database, without waiting for the next app
restart (app.py now also runs the autofill step automatically on every
startup, but this lets you apply it right now and backfill history too).

What it does:
  1. Fills in category-based nutrition estimates for any food that
     currently has no nutrition data at all (see
     nutrition_autofill_service.py -- never touches foods a restaurant
     has already filled in).
  2. Retroactively creates a NutritionLog entry for every past order that
     now has nutrition data, for every customer, so your "2-3 past
     orders" show up on the Nutrition page immediately instead of only
     counting future orders you manually click "Add to nutrition log" on.

Usage (from the food-delivery-app/ directory):
    python -m backend.utils.fix_nutrition_now
"""
from backend.app import create_app
from backend.models.models import db, Order
from backend.services.nutrition_autofill_service import autofill_missing_nutrition
from backend.services import nutrition_service


def backfill_logs_for_all_orders():
    orders = Order.query.all()
    logged = 0
    skipped = 0
    for order in orders:
        preview = nutrition_service.order_nutrition_preview(order)
        if not preview["has_nutrition_data"]:
            skipped += 1
            continue
        try:
            nutrition_service.log_order(order.customer_id, order.id)
            logged += 1
        except ValueError:
            skipped += 1
    return logged, skipped


def main():
    app = create_app()
    with app.app_context():
        filled = autofill_missing_nutrition()
        print(f"Filled nutrition estimates for {filled} food item(s).")

        logged, skipped = backfill_logs_for_all_orders()
        print(f"Backfilled nutrition logs for {logged} order(s); "
              f"{skipped} order(s) skipped (no nutrition data or already logged).")


if __name__ == "__main__":
    main()