"""
Mood tags and ingredient/allergen tags for food items.

Both are simple many-to-many tag systems on Food, seeded with a fixed
starter list by the migration (see database/migrations/011_batch1_features.sql)
so the customer-facing filter UI stays consistent. Admin can activate/
deactivate a tag; restaurants assign tags to their own food items.
"""
from backend.models.models import db, FoodMood, FoodAllergen, FoodMoodMapping, FoodAllergenMapping, Food

ALLERGEN_DISCLAIMER = (
    "Ingredient and allergen information is provided by the restaurant. "
    "Customers with allergies should confirm directly with the restaurant."
)

DEFAULT_MOODS = [
    ("Comfort Food", "🍲"), ("Post-Workout", "💪"), ("Light & Healthy", "🥗"),
    ("Spicy Craving", "🌶️"), ("Sweet Craving", "🍰"), ("Quick Bite", "⚡"),
    ("Late Night", "🌙"), ("Family Meal", "👨‍👩‍👧‍👦"), ("Budget Friendly", "💰"),
    ("Energy Boost", "🔋"),
]

DEFAULT_ALLERGENS = [
    "Vegan", "Jain", "Nut-free", "Dairy-free", "Gluten-free",
    "Contains Nuts", "Contains Dairy", "Contains Gluten", "Spicy",
]


def ensure_default_moods():
    """Idempotent: inserts any moods that don't already exist by name, AND
    repairs the emoji on ones that do exist.

    The emoji repair matters because on some setups the moods were first
    created via the raw SQL migration (database/migrations/011_batch1_features.sql)
    run through a MySQL client that wasn't forced onto a utf8mb4 connection.
    In that case the emoji bytes get mangled ("mojibake") on insert and, since
    this function used to only add *missing* rows, the corrupted values were
    never corrected. We now always re-sync the emoji to the known-good value
    from DEFAULT_MOODS so the UI self-heals on the next app start."""
    existing = {m.name: m for m in FoodMood.query.all()}
    changed = False
    for name, emoji in DEFAULT_MOODS:
        m = existing.get(name)
        if m is None:
            db.session.add(FoodMood(name=name, emoji=emoji))
            changed = True
        elif m.emoji != emoji:
            m.emoji = emoji
            changed = True
    if changed:
        db.session.commit()


# Keyword -> mood name heuristics used to auto-tag existing/seeded foods that
# have no mood assigned yet, so the "What are you feeling?" filter actually
# returns results out of the box. Restaurants can still override tags per-item
# via set_food_moods(); this only fills in foods that currently have none.
MOOD_KEYWORD_RULES = [
    ("Spicy Craving", ["spicy", "chilli", "chili", "peri peri", "masala", "tandoori", "vindaloo"]),
    ("Sweet Craving", ["cake", "dessert", "brownie", "ice cream", "gulab jamun", "kheer", "pastry", "chocolate", "rasgulla"]),
    ("Late Night", ["maggi", "roll", "shawarma", "fried rice", "noodles"]),
    ("Quick Bite", ["sandwich", "wrap", "roll", "burger", "puff", "vada pav"]),
    ("Comfort Food", ["biryani", "thali", "curry", "dal", "khichdi", "soup", "pasta"]),
    ("Light & Healthy", ["salad", "grilled", "soup", "sprouts", "fruit"]),
    ("Post-Workout", ["grilled chicken", "egg", "paneer", "protein", "grilled"]),
    ("Family Meal", ["thali", "combo", "family pack", "pizza", "biryani"]),
    ("Energy Boost", ["coffee", "smoothie", "shake", "juice", "energy"]),
    ("Budget Friendly", []),  # handled separately by price, see below
]

BUDGET_FRIENDLY_MAX_PRICE = 150


def auto_tag_untagged_foods():
    """Best-effort, idempotent: for any food that currently has ZERO mood
    tags, assign moods by matching keywords in its name (and price, for
    'Budget Friendly'). Foods that already have at least one mood tag are
    left untouched, so this never clobbers a restaurant's own tagging."""
    moods_by_name = {m.name: m for m in FoodMood.query.all()}
    if not moods_by_name:
        return

    tagged_food_ids = {fid for (fid,) in db.session.query(FoodMoodMapping.food_id).distinct()}
    untagged_foods = Food.query.filter(~Food.id.in_(tagged_food_ids)).all() if tagged_food_ids \
        else Food.query.all()

    changed = False
    for food in untagged_foods:
        name_lower = (food.name or "").lower()
        matched_mood_ids = set()

        for mood_name, keywords in MOOD_KEYWORD_RULES:
            mood = moods_by_name.get(mood_name)
            if not mood:
                continue
            if any(kw in name_lower for kw in keywords):
                matched_mood_ids.add(mood.id)

        budget_mood = moods_by_name.get("Budget Friendly")
        if budget_mood and food.price is not None and float(food.price) <= BUDGET_FRIENDLY_MAX_PRICE:
            matched_mood_ids.add(budget_mood.id)

        # Fallback so every food gets at least one mood tag, otherwise a
        # "Quick Bite" default (rather than leaving it with zero tags).
        if not matched_mood_ids:
            quick_bite = moods_by_name.get("Quick Bite")
            if quick_bite:
                matched_mood_ids.add(quick_bite.id)

        for mid in matched_mood_ids:
            db.session.add(FoodMoodMapping(food_id=food.id, mood_id=mid))
            changed = True

    if changed:
        db.session.commit()


def ensure_default_allergens():
    existing = {a.name for a in FoodAllergen.query.all()}
    for name in DEFAULT_ALLERGENS:
        if name not in existing:
            db.session.add(FoodAllergen(name=name))
    db.session.commit()


def list_active_moods():
    return FoodMood.query.filter_by(is_active=True).order_by(FoodMood.name).all()


def list_active_allergens():
    return FoodAllergen.query.filter_by(is_active=True).order_by(FoodAllergen.name).all()


def serialize_mood(m: FoodMood):
    return {"id": m.id, "name": m.name, "emoji": m.emoji, "is_active": bool(m.is_active)}


def serialize_allergen(a: FoodAllergen):
    return {"id": a.id, "name": a.name, "is_active": bool(a.is_active)}


def get_food_moods(food_id):
    return [m.mood for m in FoodMoodMapping.query.filter_by(food_id=food_id).all()]


def get_food_allergens(food_id):
    return [a.allergen for a in FoodAllergenMapping.query.filter_by(food_id=food_id).all()]


def set_food_moods(food_id, mood_ids):
    """Replace a food's mood tags with exactly the given (valid, active) set."""
    if mood_ids is None:
        return
    valid_ids = {m.id for m in FoodMood.query.filter(FoodMood.id.in_(mood_ids)).all()}
    FoodMoodMapping.query.filter_by(food_id=food_id).delete()
    for mid in valid_ids:
        db.session.add(FoodMoodMapping(food_id=food_id, mood_id=mid))


def set_food_allergens(food_id, allergen_ids):
    """Replace a food's allergen tags with exactly the given (valid) set."""
    if allergen_ids is None:
        return
    valid_ids = {a.id for a in FoodAllergen.query.filter(FoodAllergen.id.in_(allergen_ids)).all()}
    FoodAllergenMapping.query.filter_by(food_id=food_id).delete()
    for aid in valid_ids:
        db.session.add(FoodAllergenMapping(food_id=food_id, allergen_id=aid))