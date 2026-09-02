from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Customer, Cart, CartItem, Food, MealPlan
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.meal_planner_service import generate_meal_plan, serialize_meal_plan

meal_planner_bp = Blueprint("meal_planner", __name__, url_prefix="/api/customer/meal-planner")


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


@meal_planner_bp.route("", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.meal_planner")
def create_meal_plan():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}

    try:
        days = int(data.get("days", 5))
        meals_per_day = int(data.get("meals_per_day", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "days and meals_per_day must be integers."}), 400
    if not (1 <= days <= 14):
        return jsonify({"error": "days must be between 1 and 14."}), 400
    if not (1 <= meals_per_day <= 3):
        return jsonify({"error": "meals_per_day must be between 1 and 3."}), 400

    budget = data.get("budget")
    if budget is not None:
        try:
            budget = float(budget)
            if budget <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "budget must be a positive number."}), 400

    max_spend_per_meal = data.get("max_spend_per_meal")
    if max_spend_per_meal is not None:
        try:
            max_spend_per_meal = float(max_spend_per_meal)
            if max_spend_per_meal <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "max_spend_per_meal must be a positive number."}), 400

    is_veg = data.get("is_veg")
    if is_veg is not None:
        is_veg = bool(is_veg)

    category_id = data.get("category_id")

    plan = generate_meal_plan(
        customer, days=days, meals_per_day=meals_per_day, budget=budget,
        is_veg=is_veg, category_id=category_id, max_spend_per_meal=max_spend_per_meal,
    )
    return jsonify(serialize_meal_plan(plan)), 201


@meal_planner_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.meal_planner")
def list_meal_plans():
    customer = _get_own_customer()
    plans = MealPlan.query.filter_by(customer_id=customer.id).order_by(MealPlan.created_at.desc()).limit(20).all()
    return jsonify([serialize_meal_plan(p) for p in plans]), 200


@meal_planner_bp.route("/<int:plan_id>", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.meal_planner")
def get_meal_plan(plan_id):
    customer = _get_own_customer()
    plan = MealPlan.query.filter_by(id=plan_id, customer_id=customer.id).first()
    if not plan:
        return jsonify({"error": "Meal plan not found."}), 404
    return jsonify(serialize_meal_plan(plan)), 200


@meal_planner_bp.route("/<int:plan_id>/build-cart", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.meal_planner")
def build_cart_from_plan(plan_id):
    """Adds every still-available planned item to the customer's cart,
    re-validating availability and re-fetching the CURRENT price for each
    one -- the price shown at planning time is display-only and is never
    trusted here."""
    customer = _get_own_customer()
    plan = MealPlan.query.filter_by(id=plan_id, customer_id=customer.id).first()
    if not plan:
        return jsonify({"error": "Meal plan not found."}), 404

    cart = Cart.query.filter_by(customer_id=customer.id).first()
    existing_item = CartItem.query.filter_by(cart_id=cart.id).first()
    if existing_item:
        cart_restaurant_id = existing_item.food.restaurant_id if existing_item.food_id else existing_item.combo.restaurant_id
        if plan.restaurant_id and cart_restaurant_id != plan.restaurant_id:
            return jsonify({
                "error": "Your cart already has items from a different restaurant. "
                         "Clear your cart first, then build this plan."
            }), 409

    added, skipped = [], []
    for item in plan.items:
        if not item.food_id:
            skipped.append({"meal_label": item.meal_label, "reason": item.unavailable_reason or "No dish was assigned."})
            continue

        food = Food.query.get(item.food_id)
        if not food or not food.is_available:
            skipped.append({"meal_label": item.meal_label, "reason": "This item is currently unavailable."})
            continue
        if food.track_inventory and (food.stock_quantity or 0) < item.quantity:
            skipped.append({"meal_label": item.meal_label, "reason": "This item is currently unavailable."})
            continue

        existing = CartItem.query.filter_by(cart_id=cart.id, food_id=food.id).first()
        if existing:
            existing.quantity += item.quantity
        else:
            db.session.add(CartItem(cart_id=cart.id, food_id=food.id, quantity=item.quantity))

        added.append({"food_id": food.id, "name": food.name, "quantity": item.quantity, "current_price": food.final_price})

    db.session.commit()
    return jsonify({"added": added, "skipped": skipped}), 200
