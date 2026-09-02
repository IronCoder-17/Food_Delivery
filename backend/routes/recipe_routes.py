from flask import Blueprint, request, jsonify

from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services import recipe_service

recipe_bp = Blueprint("recipe", __name__, url_prefix="/api/customer/recipe-match")


@recipe_bp.route("/url", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.recipe_to_order")
def match_from_url():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url is required."}), 400

    try:
        ingredients, used_ai = recipe_service.extract_ingredients_from_url(url)
    except ValueError as e:
        return jsonify({"error": str(e), "needs_manual_input": True}), 200

    matches = recipe_service.match_ingredients_to_foods(ingredients)
    return jsonify({
        "ingredients": ingredients,
        "used_ai": used_ai,
        "matches": matches,
        "needs_manual_input": False,
    }), 200


@recipe_bp.route("/manual", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.recipe_to_order")
def match_from_manual_ingredients():
    data = request.get_json(force=True) or {}
    ingredients = data.get("ingredients")
    if not isinstance(ingredients, list) or not ingredients:
        return jsonify({"error": "ingredients must be a non-empty list of strings."}), 400

    matches = recipe_service.match_ingredients_to_foods(ingredients)
    return jsonify({"ingredients": ingredients, "used_ai": False, "matches": matches}), 200
