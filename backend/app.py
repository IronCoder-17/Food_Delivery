import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from backend.config.config import Config
from backend.models.models import db

from backend.routes.auth_routes import auth_bp
from backend.routes.location_routes import location_bp
from backend.routes.food_routes import food_bp
from backend.routes.cart_routes import cart_bp
from backend.routes.order_routes import order_bp
from backend.routes.payment_routes import payment_bp
from backend.routes.wallet_routes import wallet_bp
from backend.routes.game_routes import game_bp
from backend.routes.restaurant_routes import restaurant_bp
from backend.routes.admin_routes import admin_bp
from backend.routes.customer_routes import customer_bp

from backend.routes.ai_routes import ai_bp
from backend.routes.loyalty_routes import loyalty_bp
from backend.routes.self_authority_routes import customer_authority_bp, restaurant_authority_bp
from backend.routes.admin_authority_routes import admin_authority_bp
from backend.routes.admin_loyalty_routes import admin_loyalty_bp
from backend.routes.address_routes import address_bp
from backend.routes.favorite_routes import favorite_bp
from backend.routes.review_routes import review_bp, restaurant_review_bp, public_review_bp, admin_review_bp
from backend.routes.combo_routes import combo_bp, public_combo_bp
from backend.routes.flash_sale_routes import flash_sale_bp
from backend.routes.reorder_routes import reorder_bp
from backend.routes.scheduled_order_routes import scheduled_order_bp
from backend.routes.meal_planner_routes import meal_planner_bp
from backend.routes.group_order_routes import group_order_bp
from backend.routes.referral_routes import referral_bp
from backend.routes.admin_referral_routes import admin_referral_bp
from backend.routes.pass_routes import pass_bp
from backend.routes.admin_pass_routes import admin_pass_bp
from backend.routes.subscription_routes import subscription_bp
from backend.routes.admin_subscription_routes import admin_subscription_bp
from backend.routes.sponsored_routes import sponsored_bp, public_sponsored_bp
from backend.routes.admin_fraud_routes import admin_fraud_bp
from backend.routes.admin_analytics_routes import admin_analytics_bp
from backend.routes.admin_promotion_routes import admin_promotion_bp
from backend.routes.dispute_routes import dispute_bp
from backend.routes.admin_dispute_routes import admin_dispute_bp
from backend.routes.mood_routes import mood_bp
from backend.routes.allergen_routes import allergen_bp
from backend.routes.kitchen_routes import kitchen_bp
from backend.routes.chef_special_routes import chef_special_bp, public_chef_special_bp, admin_chef_special_bp
from backend.routes.streak_routes import streak_bp
from backend.routes.surplus_routes import surplus_bp, public_surplus_bp, admin_surplus_bp
from backend.routes.packing_proof_routes import packing_proof_bp
from backend.routes.recipe_routes import recipe_bp
from backend.routes.photo_reorder_routes import photo_reorder_bp
from backend.routes.nutrition_routes import nutrition_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)

    for bp in [auth_bp, location_bp, food_bp, cart_bp, order_bp, payment_bp,
               wallet_bp, game_bp, restaurant_bp, admin_bp, customer_bp,
               ai_bp, loyalty_bp, customer_authority_bp, restaurant_authority_bp,
               admin_authority_bp, admin_loyalty_bp,
               address_bp, favorite_bp, review_bp, restaurant_review_bp,
               public_review_bp, admin_review_bp,
               combo_bp, public_combo_bp, flash_sale_bp, reorder_bp, scheduled_order_bp, meal_planner_bp,
               group_order_bp, referral_bp, admin_referral_bp,
               pass_bp, admin_pass_bp, subscription_bp, admin_subscription_bp, sponsored_bp, public_sponsored_bp,
               admin_fraud_bp, admin_analytics_bp, admin_promotion_bp, dispute_bp, admin_dispute_bp,
               mood_bp, allergen_bp, kitchen_bp, chef_special_bp, public_chef_special_bp,
               admin_chef_special_bp, streak_bp, surplus_bp, public_surplus_bp, admin_surplus_bp,
               packing_proof_bp, recipe_bp, photo_reorder_bp, nutrition_bp]:
        app.register_blueprint(bp)

    with app.app_context():
        # Idempotent startup seeding: creates the loyalty rank ladder and the
        # full authority permission catalog if they don't exist yet. Does
        # NOT touch per-user authority rows (those are created at
        # registration time in auth_routes.py) or existing loyalty data.
        try:
            db.create_all()
            from backend.services.loyalty_service import ensure_default_levels
            from backend.services.authority_service import ensure_default_permissions
            from backend.services.food_tags_service import (
                ensure_default_moods, ensure_default_allergens, auto_tag_untagged_foods,
            )
            ensure_default_levels()
            ensure_default_permissions()
            ensure_default_moods()
            ensure_default_allergens()
            # Backfill mood tags for any food that has none yet, so the
            # "What are you feeling?" filter returns results out of the box
            # instead of "No dishes found" for every mood.
            auto_tag_untagged_foods()
            # Backfill nutrition estimates for any food with no nutrition
            # data at all, so Nutrition Tracking has something to log
            # instead of showing all zeros no matter how many orders are
            # placed. Foods a restaurant has already filled in are untouched.
            # from backend.services.nutrition_autofill_service import autofill_missing_nutrition
            # autofill_missing_nutrition()
        except Exception as e:
            # Don't crash app boot if the DB isn't reachable yet at import
            # time (e.g. first deploy before migrations); log and continue.
            app.logger.warning(f"Startup seeding skipped: {e}")

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "database": app.config["SQLALCHEMY_DATABASE_URI"].split("://")[0]}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return jsonify({"error": "Internal server error. Please try again."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # threaded=True so a slow outbound call (e.g. the AI Assistant waiting on
    # OpenRouter) doesn't block every other request on this single dev server.
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "1") == "1", threaded=True)