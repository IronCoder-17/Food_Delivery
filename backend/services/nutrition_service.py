"""
Optional Nutrition Tracking. Values come from restaurant-provided fields on
Food (calories/protein/carbs/fat) -- they are estimates, not verified lab
data, and never presented as medical advice. Any food missing nutrition
data simply contributes 0 to a log rather than a guessed value.
"""
from datetime import date, timedelta

from backend.models.models import db, NutritionLog, Order

NUTRITION_DISCLAIMER = (
    "Nutrition values are estimates provided by the restaurant, not verified lab "
    "data, and should not be treated as medical or dietary advice."
)


def log_order(customer_id: int, order_id: int) -> NutritionLog:
    existing = NutritionLog.query.filter_by(customer_id=customer_id, order_id=order_id).first()
    if existing:
        return existing  # idempotent -- logging the same order twice is a no-op

    order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
    if not order:
        raise ValueError("Order not found.")

    calories = protein = carbs = fat = 0
    for item in order.items:
        food = item.food
        if not food:
            continue
        calories += (food.calories or 0) * item.quantity
        protein += float(food.protein_grams or 0) * item.quantity
        carbs += float(food.carbs_grams or 0) * item.quantity
        fat += float(food.fat_grams or 0) * item.quantity

    log = NutritionLog(
        customer_id=customer_id, order_id=order_id,
        calories=round(calories), protein_grams=round(protein, 2),
        carbs_grams=round(carbs, 2), fat_grams=round(fat, 2),
        logged_date=order.created_at.date() if order.created_at else date.today(),
    )
    db.session.add(log)
    db.session.commit()
    return log


def order_nutrition_preview(order: Order):
    """Read-only preview (no DB write) shown right after an order, before
    the customer decides whether to add it to their log."""
    calories = protein = carbs = fat = 0
    any_data = False
    for item in order.items:
        food = item.food
        if not food:
            continue
        if food.calories or food.protein_grams or food.carbs_grams or food.fat_grams:
            any_data = True
        calories += (food.calories or 0) * item.quantity
        protein += float(food.protein_grams or 0) * item.quantity
        carbs += float(food.carbs_grams or 0) * item.quantity
        fat += float(food.fat_grams or 0) * item.quantity
    return {
        "calories": round(calories), "protein_grams": round(protein, 2),
        "carbs_grams": round(carbs, 2), "fat_grams": round(fat, 2),
        "has_nutrition_data": any_data,
        "disclaimer": NUTRITION_DISCLAIMER,
    }


def serialize_log(log: NutritionLog):
    return {
        "id": log.id,
        "order_id": log.order_id,
        "calories": log.calories,
        "protein_grams": float(log.protein_grams),
        "carbs_grams": float(log.carbs_grams),
        "fat_grams": float(log.fat_grams),
        "logged_date": log.logged_date.isoformat(),
    }


def _summarize(logs):
    return {
        "calories": sum(l.calories for l in logs),
        "protein_grams": round(sum(float(l.protein_grams) for l in logs), 2),
        "carbs_grams": round(sum(float(l.carbs_grams) for l in logs), 2),
        "fat_grams": round(sum(float(l.fat_grams) for l in logs), 2),
        "order_count": len(logs),
    }


def daily_summary(customer_id: int, day: date = None):
    day = day or date.today()
    logs = NutritionLog.query.filter_by(customer_id=customer_id, logged_date=day).all()
    return {"date": day.isoformat(), **_summarize(logs), "disclaimer": NUTRITION_DISCLAIMER}


def weekly_summary(customer_id: int, end_day: date = None):
    end_day = end_day or date.today()
    start_day = end_day - timedelta(days=6)
    logs = NutritionLog.query.filter(
        NutritionLog.customer_id == customer_id,
        NutritionLog.logged_date >= start_day,
        NutritionLog.logged_date <= end_day,
    ).all()
    return {
        "start_date": start_day.isoformat(), "end_date": end_day.isoformat(),
        **_summarize(logs), "disclaimer": NUTRITION_DISCLAIMER,
    }


def export_logs(customer_id: int):
    """Returns only this customer's own logs -- never another customer's."""
    logs = NutritionLog.query.filter_by(customer_id=customer_id).order_by(NutritionLog.logged_date.desc()).all()
    return [serialize_log(l) for l in logs]
