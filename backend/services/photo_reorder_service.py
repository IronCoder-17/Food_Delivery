"""
Photo Reorder. Customer uploads a photo of a dish (theirs or a friend's);
we identify the dish + likely ingredients via the same configured AI
provider used by AI Assistant / Recipe-to-Order, then reuse the exact same
deterministic ingredient-to-menu matching from recipe_service -- no
duplicated matching logic, no second AI-guessing step for the actual menu
match.

Design notes (same honesty standard as recipe_service):
  - If no AI provider is configured, this feature is plainly UNAVAILABLE.
    It never fabricates a dish name or ingredient list.
  - "Nearby" restaurants: this app has no restaurant geo-coordinates (only
    city_id), so "nearby" honestly means "same city as the customer's
    profile", never a fabricated distance figure. If the customer has no
    city set, we fall back to all restaurants and say so.
"""
import re

from backend.models.models import Food, Customer
from backend.services import ai_service
from backend.services.recipe_service import match_ingredients_to_foods

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image(file_storage):
    """Raises ValueError with a user-facing message on any problem. Returns
    (bytes, mime_type) on success."""
    if not file_storage or not file_storage.filename:
        raise ValueError("No image file provided.")

    mime_type = (file_storage.mimetype or "").lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported image type. Please upload a JPEG, PNG, or WEBP photo.")

    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size == 0:
        raise ValueError("Uploaded file is empty.")
    if size > MAX_IMAGE_BYTES:
        raise ValueError("Image is too large (max 5 MB).")

    return file_storage.read(), mime_type


def _boost_by_dish_name(results: list, dish_name: str, foods_by_id: dict):
    """Ingredient matching alone can miss/underweight the dish itself (e.g.
    a photo of "Margherita Pizza" whose ingredients partially overlap many
    menu items). Also do a direct, deterministic name match and merge it in
    -- never an AI guess, just substring matching against real menu text."""
    if not dish_name:
        return results

    name_lower = dish_name.strip().lower()
    if not name_lower:
        return results

    existing_ids = {r["food_id"] for r in results}
    name_matches = []
    candidates = foods_by_id.values()
    for food in candidates:
        haystack = food.name.lower()
        if name_lower in haystack or haystack in name_lower:
            if food.id in existing_ids:
                continue
            name_matches.append({
                "food_id": food.id,
                "food_name": food.name,
                "restaurant_id": food.restaurant_id,
                "restaurant_name": food.restaurant.restaurant_name if food.restaurant else None,
                "price": float(food.final_price),
                "is_available": bool(food.is_available),
                "matched_ingredients": [],
                "match_percent": 100.0,  # direct dish-name match, ranked first
                "matched_by": "dish_name",
            })

    return name_matches + results


def match_photo_to_menu(customer: Customer, image_bytes: bytes, mime_type: str, nearby_only: bool = True):
    """Returns a dict: {dish_name, ingredients, matches, nearby_applied, used_ai}.
    Raises ValueError (user-facing) if the AI provider can't identify the
    dish -- callers should offer a manual dish-name/ingredient fallback,
    exactly like Recipe-to-Order does for URLs."""
    try:
        identified = ai_service.identify_dish_from_image(image_bytes, mime_type)
    except ai_service.AiServiceError as e:
        raise ValueError(
            f"Couldn't identify that photo automatically ({e}). "
            "Try a clearer photo, or search for the dish by name instead."
        )

    dish_name = identified["dish_name"]
    ingredients = identified["ingredients"]

    # Ingredient-based matching first (reuses Recipe-to-Order's real DB
    # query, not a second AI call).
    base_matches = match_ingredients_to_foods(ingredients, limit=40) if ingredients else []

    all_foods = Food.query.filter_by(is_available=True).all()
    foods_by_id = {f.id: f for f in all_foods}
    merged = _boost_by_dish_name(base_matches, dish_name, foods_by_id)

    nearby_applied = False
    if nearby_only and customer.city_id:
        restaurant_ids_in_city = {
            f.restaurant_id for f in all_foods
            if f.restaurant and f.restaurant.city_id == customer.city_id
        }
        filtered = [m for m in merged if m["restaurant_id"] in restaurant_ids_in_city]
        # Only apply the filter if it actually leaves something -- otherwise
        # showing zero results because of a city mismatch is worse than
        # showing the full, honestly-labeled list.
        if filtered:
            merged = filtered
            nearby_applied = True

    return {
        "dish_name": dish_name,
        "ingredients": ingredients,
        "matches": merged[:20],
        "nearby_applied": nearby_applied,
        "used_ai": True,
    }


def match_dish_name_to_menu(dish_name: str, nearby_only: bool, customer: Customer):
    """Manual fallback (no photo/AI): direct dish-name search, same
    honesty/no-fabrication standard -- a real query against the live menu."""
    name_lower = (dish_name or "").strip().lower()
    if not name_lower:
        return {"dish_name": dish_name, "ingredients": [], "matches": [], "nearby_applied": False, "used_ai": False}

    foods = Food.query.filter_by(is_available=True).all()
    matches = []
    for food in foods:
        if re.search(re.escape(name_lower), food.name.lower()):
            matches.append({
                "food_id": food.id,
                "food_name": food.name,
                "restaurant_id": food.restaurant_id,
                "restaurant_name": food.restaurant.restaurant_name if food.restaurant else None,
                "price": float(food.final_price),
                "is_available": bool(food.is_available),
                "matched_ingredients": [],
                "match_percent": 100.0,
                "matched_by": "dish_name",
            })

    nearby_applied = False
    if nearby_only and customer.city_id:
        restaurant_ids_in_city = {
            f.restaurant_id for f in foods if f.restaurant and f.restaurant.city_id == customer.city_id
        }
        filtered = [m for m in matches if m["restaurant_id"] in restaurant_ids_in_city]
        if filtered:
            matches = filtered
            nearby_applied = True

    return {"dish_name": dish_name, "ingredients": [], "matches": matches[:20], "nearby_applied": nearby_applied, "used_ai": False}
