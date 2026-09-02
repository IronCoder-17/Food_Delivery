"""
Sponsored / Featured Restaurants. Admin-controlled placements, always
clearly labeled "Sponsored" wherever shown to a customer -- never merged
into organic search/ranking results without that label.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify

from backend.models.models import db, Restaurant, SponsoredCampaign
from backend.middleware.auth_middleware import token_required

sponsored_bp = Blueprint("sponsored", __name__, url_prefix="/api/admin/sponsored")
public_sponsored_bp = Blueprint("public_sponsored", __name__, url_prefix="/api/sponsored")


def _serialize(c: SponsoredCampaign):
    return {
        "id": c.id,
        "restaurant_id": c.restaurant_id,
        "restaurant_name": c.restaurant.restaurant_name if c.restaurant else None,
        "placement": c.placement,
        "priority": c.priority,
        "budget": float(c.budget) if c.budget is not None else None,
        "campaign_start": c.campaign_start.isoformat(),
        "campaign_end": c.campaign_end.isoformat(),
        "is_active": bool(c.is_active),
        "is_currently_live": c.is_currently_live(),
    }


def _parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@public_sponsored_bp.route("", methods=["GET"])
def public_list_sponsored():
    placement = request.args.get("placement", "homepage")
    campaigns = SponsoredCampaign.query.filter_by(placement=placement, is_active=True).all()
    live = [c for c in campaigns if c.is_currently_live() and c.restaurant and c.restaurant.status == "approved"]
    live.sort(key=lambda c: c.priority, reverse=True)
    return jsonify([{
        "restaurant_id": c.restaurant_id,
        "restaurant_name": c.restaurant.restaurant_name,
        "logo_url": c.restaurant.logo_url,
        "cover_image_url": c.restaurant.cover_image_url,
        "rating": float(c.restaurant.rating or 0),
        "sponsored": True,  # explicit flag so the frontend can never accidentally render this as organic
    } for c in live]), 200


@sponsored_bp.route("", methods=["GET"])
@token_required(["admin"])
def admin_list_sponsored():
    campaigns = SponsoredCampaign.query.order_by(SponsoredCampaign.created_at.desc()).all()
    return jsonify([_serialize(c) for c in campaigns]), 200


@sponsored_bp.route("", methods=["POST"])
@token_required(["admin"])
def create_sponsored_campaign():
    data = request.get_json(force=True) or {}
    restaurant = Restaurant.query.filter_by(id=data.get("restaurant_id"), status="approved").first()
    if not restaurant:
        return jsonify({"error": "Restaurant not found or not approved."}), 404

    start = _parse_dt(data.get("campaign_start"))
    end = _parse_dt(data.get("campaign_end"))
    if not start or not end:
        return jsonify({"error": "Valid campaign_start and campaign_end (ISO 8601) are required."}), 400
    if end <= start:
        return jsonify({"error": "campaign_end must be after campaign_start."}), 400

    budget = data.get("budget")
    if budget is not None:
        try:
            budget = float(budget)
        except (TypeError, ValueError):
            return jsonify({"error": "budget must be a number."}), 400

    campaign = SponsoredCampaign(
        restaurant_id=restaurant.id, placement=data.get("placement", "homepage"),
        priority=int(data.get("priority", 0)), budget=budget,
        campaign_start=start, campaign_end=end, is_active=bool(data.get("is_active", True)),
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify(_serialize(campaign)), 201


@sponsored_bp.route("/<int:campaign_id>", methods=["PUT"])
@token_required(["admin"])
def update_sponsored_campaign(campaign_id):
    campaign = SponsoredCampaign.query.get(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found."}), 404
    data = request.get_json(force=True) or {}

    if "placement" in data:
        campaign.placement = data["placement"]
    if "priority" in data:
        campaign.priority = int(data["priority"])
    if "budget" in data:
        campaign.budget = float(data["budget"]) if data["budget"] is not None else None
    if "campaign_start" in data:
        dt = _parse_dt(data["campaign_start"])
        if not dt:
            return jsonify({"error": "Invalid campaign_start."}), 400
        campaign.campaign_start = dt
    if "campaign_end" in data:
        dt = _parse_dt(data["campaign_end"])
        if not dt:
            return jsonify({"error": "Invalid campaign_end."}), 400
        campaign.campaign_end = dt
    if campaign.campaign_end <= campaign.campaign_start:
        return jsonify({"error": "campaign_end must be after campaign_start."}), 400
    if "is_active" in data:
        campaign.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(_serialize(campaign)), 200


@sponsored_bp.route("/<int:campaign_id>", methods=["DELETE"])
@token_required(["admin"])
def delete_sponsored_campaign(campaign_id):
    campaign = SponsoredCampaign.query.get(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found."}), 404
    db.session.delete(campaign)
    db.session.commit()
    return jsonify({"message": "Campaign deleted."}), 200
