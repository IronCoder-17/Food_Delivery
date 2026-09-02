from datetime import datetime

from flask import Blueprint, request, jsonify

from backend.models.models import db, PromotionExperiment
from backend.middleware.auth_middleware import token_required
from backend.services.promotion_service import serialize_experiment

admin_promotion_bp = Blueprint("admin_promotion", __name__, url_prefix="/api/admin/promotions")


def _parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@admin_promotion_bp.route("", methods=["GET"])
@token_required(["admin"])
def list_experiments():
    experiments = PromotionExperiment.query.order_by(PromotionExperiment.created_at.desc()).all()
    return jsonify([serialize_experiment(e, include_stats=True) for e in experiments]), 200


@admin_promotion_bp.route("", methods=["POST"])
@token_required(["admin"])
def create_experiment():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Experiment name is required."}), 400

    # Only one experiment may run at a time -- see promotion_service docstring.
    if PromotionExperiment.query.filter_by(status="running").first():
        return jsonify({"error": "Another experiment is already running. Complete it before starting a new one."}), 400

    try:
        disc_a = float(data.get("discount_percent_a", 0))
        disc_b = float(data.get("discount_percent_b", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "discount_percent_a/b must be numbers."}), 400

    experiment = PromotionExperiment(
        name=name,
        variant_a_label=data.get("variant_a_label", "Promotion A"),
        variant_b_label=data.get("variant_b_label", "Promotion B"),
        discount_percent_a=disc_a, discount_percent_b=disc_b,
        status=data.get("status", "draft"),
        start_date=_parse_dt(data.get("start_date")), end_date=_parse_dt(data.get("end_date")),
    )
    db.session.add(experiment)
    db.session.commit()
    return jsonify(serialize_experiment(experiment)), 201


@admin_promotion_bp.route("/<int:experiment_id>/status", methods=["PUT"])
@token_required(["admin"])
def set_experiment_status(experiment_id):
    experiment = PromotionExperiment.query.get(experiment_id)
    if not experiment:
        return jsonify({"error": "Experiment not found."}), 404
    data = request.get_json(force=True) or {}
    new_status = data.get("status")
    if new_status not in ("draft", "running", "completed"):
        return jsonify({"error": "Status must be draft, running, or completed."}), 400
    if new_status == "running":
        other = PromotionExperiment.query.filter(
            PromotionExperiment.status == "running", PromotionExperiment.id != experiment.id
        ).first()
        if other:
            return jsonify({"error": f"Experiment '{other.name}' is already running."}), 400
    experiment.status = new_status
    db.session.commit()
    return jsonify(serialize_experiment(experiment, include_stats=True)), 200
