from flask import Blueprint, jsonify
from backend.models.models import State, City

location_bp = Blueprint("location", __name__, url_prefix="/api/locations")


@location_bp.route("/states", methods=["GET"])
def get_states():
    states = State.query.order_by(State.name).all()
    return jsonify([{"id": s.id, "name": s.name} for s in states]), 200


@location_bp.route("/states/<int:state_id>/cities", methods=["GET"])
def get_cities(state_id):
    cities = City.query.filter_by(state_id=state_id).order_by(City.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in cities]), 200
