"""
AI Meal Planner -- the actual food/restaurant/price selection is 100%
deterministic and reads only from the live Food table. This is a deliberate
design choice, not a shortcut: an LLM call is inherently capable of
inventing a restaurant, dish, or price, and the spec is explicit that this
must never happen. So the "AI" here means the *planning logic* (constraint
solving across days/meals/budget/preferences), not a language model
choosing dishes. The optional narration line at the end is the only place
an LLM is invoked, and only to phrase a short intro around the ALREADY-
CHOSEN, ALREADY-GROUNDED plan -- never to pick items itself.
"""
from datetime import datetime

from backend.models.models import db, Food, Restaurant, MealPlan, MealPlanItem
from backend.services.pricing_service import effective_food_price


def _candidate_foods(is_veg, max_spend_per_meal, category_id):
    q = Food.query.join(Restaurant).filter(Restaurant.status == "approved", Food.is_available == True)  # noqa: E712
    if is_veg is not None:
        q = q.filter(Food.is_veg == is_veg)
    if category_id:
        q = q.filter(Food.category_id == category_id)
    foods = q.all()
    # filter by *effective* (flash-sale-aware) price, not just listed price
    result = []
    for f in foods:
        if f.track_inventory and (f.stock_quantity or 0) <= 0:
            continue
        price, _ = effective_food_price(f)
        if max_spend_per_meal is not None and price > float(max_spend_per_meal):
            continue
        result.append((f, price))
    return result


def _pick_restaurant(candidates):
    """Meal plans are built from a single restaurant (checkout is
    single-restaurant in this app). Choose whichever approved restaurant has
    the most qualifying items, so the plan has real variety instead of
    forcing repeats."""
    by_restaurant = {}
    for food, price in candidates:
        by_restaurant.setdefault(food.restaurant_id, []).append((food, price))
    if not by_restaurant:
        return None, []
    best_restaurant_id = max(by_restaurant, key=lambda rid: len(by_restaurant[rid]))
    items = by_restaurant[best_restaurant_id]
    # prefer variety: sort by rating desc so better-rated dishes appear first
    items.sort(key=lambda t: float(t[0].rating or 0), reverse=True)
    return best_restaurant_id, items


MEAL_LABELS_BY_COUNT = {
    1: ["Meal"], 2: ["Lunch", "Dinner"], 3: ["Breakfast", "Lunch", "Dinner"],
}


def _meal_label(meals_per_day, meal_index):
    labels = MEAL_LABELS_BY_COUNT.get(meals_per_day)
    if labels:
        return labels[meal_index]
    return f"Meal {meal_index + 1}"


def generate_meal_plan(customer, days, meals_per_day, budget, is_veg, category_id, max_spend_per_meal):
    """
    Builds a MealPlan + MealPlanItem rows for `customer`, choosing only from
    real, currently-available Food rows. If a per-meal budget cap is
    implied by the overall budget, we derive one and apply it as an extra
    filter so the plan doesn't blow past what the customer asked for.
    """
    total_meals = days * meals_per_day

    effective_max_per_meal = max_spend_per_meal
    if budget and not max_spend_per_meal:
        # Derive an implicit per-meal ceiling from the overall budget, with
        # a little headroom (1.15x) so a slightly pricier dish can still be
        # picked on a day where a cheaper one balances it out.
        effective_max_per_meal = round(float(budget) / total_meals * 1.15, 2)

    candidates = _candidate_foods(is_veg, effective_max_per_meal, category_id)
    restaurant_id, ranked_items = _pick_restaurant(candidates)

    plan = MealPlan(
        customer_id=customer.id, restaurant_id=restaurant_id, days=days, meals_per_day=meals_per_day,
        budget=budget, is_veg=is_veg, max_spend_per_meal=max_spend_per_meal, estimated_total=0,
    )
    db.session.add(plan)
    db.session.flush()

    running_total = 0.0
    remaining_budget = float(budget) if budget else None
    cycle_pos = 0  # walks through ranked_items to spread variety across the week

    for day in range(days):
        for meal_idx in range(meals_per_day):
            label = _meal_label(meals_per_day, meal_idx)

            if not ranked_items:
                db.session.add(MealPlanItem(
                    meal_plan_id=plan.id, day_index=day, meal_index=meal_idx, meal_label=label,
                    food_id=None, unavailable_reason="No matching dishes found for your preferences.",
                ))
                continue

            # Try, in order starting from the current cycle position, to find
            # a dish that still fits the remaining budget (if any). This keeps
            # variety (round-robin) while never exceeding what's left.
            chosen = None
            for offset in range(len(ranked_items)):
                idx = (cycle_pos + offset) % len(ranked_items)
                food, price = ranked_items[idx]
                if remaining_budget is not None and price > remaining_budget:
                    continue
                chosen = (food, price)
                cycle_pos = idx + 1
                break

            if not chosen:
                # Nothing fits what's left of the budget -- be honest about it
                # rather than silently going over.
                db.session.add(MealPlanItem(
                    meal_plan_id=plan.id, day_index=day, meal_index=meal_idx, meal_label=label,
                    food_id=None, unavailable_reason="Remaining budget too low for any available dish.",
                ))
                continue

            food, price = chosen
            db.session.add(MealPlanItem(
                meal_plan_id=plan.id, day_index=day, meal_index=meal_idx, meal_label=label,
                food_id=food.id, quantity=1, price_at_planning=price,
            ))
            running_total += price
            if remaining_budget is not None:
                remaining_budget -= price

    plan.estimated_total = round(running_total, 2)
    plan.summary_note = _narrate(plan, restaurant_id, budget)
    db.session.commit()
    return plan


def _narrate(plan, restaurant_id, budget):
    """A short, template-based summary line. Deliberately NOT an LLM call --
    every number here is already computed from real data above, so there is
    nothing left for a model to get right or wrong; a template is faster,
    free, and can't drift from the numbers it's describing."""
    restaurant = Restaurant.query.get(restaurant_id) if restaurant_id else None
    parts = [f"Here's your {plan.days}-day plan"]
    if restaurant:
        parts.append(f"from {restaurant.restaurant_name}")
    parts.append(f"— estimated total ₹{plan.estimated_total}")
    if budget:
        diff = float(budget) - float(plan.estimated_total)
        if diff >= 0:
            parts.append(f"(₹{round(diff, 2)} under your ₹{budget} budget).")
        else:
            parts.append(f"(₹{round(-diff, 2)} over your ₹{budget} budget — consider raising it or narrowing preferences).")
    else:
        parts.append(".")
    return " ".join(parts)


def serialize_meal_plan(plan: MealPlan):
    days_out = {}
    for item in plan.items:
        days_out.setdefault(item.day_index, []).append({
            "meal_index": item.meal_index,
            "meal_label": item.meal_label,
            "food_id": item.food_id,
            "food_name": item.food.name if item.food else None,
            "restaurant_name": item.food.restaurant.restaurant_name if item.food and item.food.restaurant else None,
            "price": float(item.price_at_planning) if item.price_at_planning is not None else None,
            "quantity": item.quantity,
            "unavailable_reason": item.unavailable_reason,
        })
    return {
        "id": plan.id,
        "restaurant_id": plan.restaurant_id,
        "restaurant_name": plan.restaurant.restaurant_name if plan.restaurant else None,
        "days": plan.days,
        "meals_per_day": plan.meals_per_day,
        "budget": float(plan.budget) if plan.budget is not None else None,
        "is_veg": plan.is_veg,
        "estimated_total": float(plan.estimated_total),
        "summary_note": plan.summary_note,
        "schedule": [{"day_index": d, "items": days_out[d]} for d in sorted(days_out)],
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }
