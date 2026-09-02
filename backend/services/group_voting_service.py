"""
Live Group Order Voting: an ADDITIVE layer on top of the existing
direct-add shared cart (group_order_routes.py). A host can turn voting on
for their group order; members suggest dishes and vote; when voting closes,
winning dishes (most votes) are added to the SAME shared cart the
direct-add flow already uses -- so checkout, pricing, and the rest of
group_order_routes.py needs zero changes.
"""
from backend.models.models import db, GroupOrder, GroupOrderSuggestion, GroupOrderVote, GroupOrderItem, Food


def serialize_suggestion(s: GroupOrderSuggestion, viewer_customer_id):
    return {
        "id": s.id,
        "food_id": s.food_id,
        "food_name": s.food.name if s.food else "Unavailable item",
        "food_image_url": s.food.image_url if s.food else None,
        "suggested_by_customer_id": s.suggested_by_customer_id,
        "suggested_by_name": f"{s.suggested_by.first_name} {s.suggested_by.last_name[0]}." if s.suggested_by else "Member",
        "vote_count": len(s.votes),
        "voted_by_me": any(v.customer_id == viewer_customer_id for v in s.votes),
    }


def list_suggestions(group_order_id, viewer_customer_id):
    suggestions = GroupOrderSuggestion.query.filter_by(group_order_id=group_order_id).all()
    data = [serialize_suggestion(s, viewer_customer_id) for s in suggestions]
    data.sort(key=lambda x: x["vote_count"], reverse=True)
    return data


def add_suggestion(group_order, customer_id, food_id):
    food = Food.query.filter_by(id=food_id, restaurant_id=group_order.restaurant_id).first()
    if not food or not food.is_available:
        raise ValueError("This food item is unavailable at this restaurant.")
    existing = GroupOrderSuggestion.query.filter_by(group_order_id=group_order.id, food_id=food_id).first()
    if existing:
        return existing  # already suggested -- just let the member vote for it
    suggestion = GroupOrderSuggestion(group_order_id=group_order.id, food_id=food_id, suggested_by_customer_id=customer_id)
    db.session.add(suggestion)
    db.session.commit()
    return suggestion


def cast_vote(suggestion: GroupOrderSuggestion, customer_id):
    existing = GroupOrderVote.query.filter_by(suggestion_id=suggestion.id, customer_id=customer_id).first()
    if existing:
        return False  # already voted -- no-op, not an error (idempotent)
    db.session.add(GroupOrderVote(suggestion_id=suggestion.id, customer_id=customer_id))
    db.session.commit()
    return True


def remove_vote(suggestion: GroupOrderSuggestion, customer_id):
    existing = GroupOrderVote.query.filter_by(suggestion_id=suggestion.id, customer_id=customer_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return True
    return False


def finalize_voting(group_order: GroupOrder):
    """Adds the winning suggestion(s) -- any suggestion with the maximum
    vote count, and only if that count is > 0 -- to the group's shared cart
    as real GroupOrderItem rows (quantity 1 each), attributed to whoever
    suggested them. Safe to call more than once: a suggestion that has
    already been converted won't be added twice, since we check for an
    existing GroupOrderItem with the same food_id first."""
    suggestions = GroupOrderSuggestion.query.filter_by(group_order_id=group_order.id).all()
    if not suggestions:
        return []

    max_votes = max(len(s.votes) for s in suggestions)
    if max_votes == 0:
        return []  # nobody voted for anything -- nothing to add

    winners = [s for s in suggestions if len(s.votes) == max_votes]
    added = []
    for w in winners:
        already_in_cart = GroupOrderItem.query.filter_by(group_order_id=group_order.id, food_id=w.food_id).first()
        if already_in_cart:
            continue
        food = Food.query.get(w.food_id)
        if not food or not food.is_available:
            continue
        item = GroupOrderItem(
            group_order_id=group_order.id, customer_id=w.suggested_by_customer_id,
            food_id=w.food_id, quantity=1,
        )
        db.session.add(item)
        added.append(w.food_id)

    db.session.commit()
    return added
