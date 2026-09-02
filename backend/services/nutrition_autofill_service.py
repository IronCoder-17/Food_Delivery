"""
Best-effort nutrition estimate auto-fill for food items.

Restaurants are meant to enter calories/protein/carbs/fat per dish
themselves, but many seeded/legacy foods have none of those fields set,
which means the customer-facing Nutrition Tracking page has nothing to log
(see nutrition_service.py -- items with no nutrition data are skipped
entirely and contribute nothing, so a customer can order repeatedly and
still see all zeros).

This module fills in a reasonable *estimate* -- based on the food's
category and veg/non-veg flag -- for any food that currently has ALL FOUR
nutrition fields empty. It intentionally:
  - Never overwrites a value a restaurant already entered (if even one of
    the four fields is set, the food is left completely untouched).
  - Is idempotent / safe to run repeatedly or on every app startup.
  - Is clearly an estimate: the UI already shows the disclaimer that
    nutrition values are estimates and not verified lab or medical data.
"""
from backend.models.models import db, Food, Category

# Per-category baseline estimates (per single serving), roughly calibrated
# to typical Indian restaurant portions. (calories, protein_g, carbs_g, fat_g)
CATEGORY_BASELINES = {
    "Pizza":         (285, 12, 36, 10),
    "Burger":        (350, 15, 33, 18),
    "Cold Drinks":   (150, 0,  38, 0),
    "Dessert":       (300, 4,  45, 12),
    "Biryani":       (420, 18, 58, 12),
    "Chinese":       (380, 14, 45, 14),
    "South Indian":  (220, 6,  35, 6),
    "Sandwich":      (280, 10, 32, 11),
    "Pasta":         (400, 12, 55, 14),
    "Snacks":        (250, 6,  28, 12),
    "Thali":         (600, 20, 80, 18),
    "Cakes":         (320, 5,  42, 14),
}

DEFAULT_BASELINE = (300, 10, 35, 12)  # used for any category not in the table above

# Non-veg dishes get a protein bump and slightly higher calories/fat,
# reflecting the added meat/egg/fish content.
NON_VEG_PROTEIN_BONUS = 8
NON_VEG_CALORIE_BONUS = 60
NON_VEG_FAT_BONUS = 5


def _estimate_for(food: Food, category_name: str):
    calories, protein, carbs, fat = CATEGORY_BASELINES.get(category_name, DEFAULT_BASELINE)
    if not food.is_veg:
        calories += NON_VEG_CALORIE_BONUS
        protein += NON_VEG_PROTEIN_BONUS
        fat += NON_VEG_FAT_BONUS
    return calories, protein, carbs, fat


def autofill_missing_nutrition():
    """For every food where calories, protein, carbs, and fat are ALL
    unset, fill in a category-based estimate. Foods with at least one
    field already set (i.e. a restaurant has started entering real data)
    are left completely alone."""
    foods = (
        Food.query.filter(
            Food.calories.is_(None),
            Food.protein_grams.is_(None),
            Food.carbs_grams.is_(None),
            Food.fat_grams.is_(None),
        )
        .all()
    )
    if not foods:
        return 0

    category_names = {c.id: c.name for c in Category.query.all()}
    changed = 0
    for food in foods:
        category_name = category_names.get(food.category_id, "")
        calories, protein, carbs, fat = _estimate_for(food, category_name)
        food.calories = calories
        food.protein_grams = protein
        food.carbs_grams = carbs
        food.fat_grams = fat
        changed += 1

    if changed:
        db.session.commit()
    return changed