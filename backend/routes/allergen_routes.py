"""
Ingredient & Allergen Tags: public read of the allergen/dietary catalog,
used by the customer filter UI. Assignment to a specific food happens in
restaurant_routes.py (add_food/update_food), reusing food_tags_service.
"""
from flask import Blueprint, jsonify

from backend.services.food_tags_service import list_active_allergens, serialize_allergen, ALLERGEN_DISCLAIMER

allergen_bp = Blueprint("allergen", __name__, url_prefix="/api/allergens")


@allergen_bp.route("", methods=["GET"])
def list_allergens():
    return jsonify({
        "allergens": [serialize_allergen(a) for a in list_active_allergens()],
        "disclaimer": ALLERGEN_DISCLAIMER,
    }), 200
