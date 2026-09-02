"""
Mood-Based Ordering: public read of the mood catalog, used by the customer
discovery UI. Assignment of moods to a specific food happens in
restaurant_routes.py (add_food/update_food), reusing food_tags_service.
"""
from flask import Blueprint, jsonify

from backend.services.food_tags_service import list_active_moods, serialize_mood

mood_bp = Blueprint("mood", __name__, url_prefix="/api/moods")


@mood_bp.route("", methods=["GET"])
def list_moods():
    return jsonify([serialize_mood(m) for m in list_active_moods()]), 200
