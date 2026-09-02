"""
Loyalty engine. All point math, rank calculation and duplicate-award
protection lives here so it behaves identically whether it's triggered by
an automatic order-completion event or a manual admin adjustment.
"""
from backend.models.models import db, LoyaltyLevel, CustomerLoyalty, LoyaltyTransaction, Order

# ---- Configurable point-earning rules -------------------------------------
# ₹100 of eligible spending = this many points (configurable here; not
# hard-coded in the frontend).
POINTS_PER_100_SPEND = 10
# Flat bonus for every successfully completed (delivered) order.
COMPLETED_ORDER_BONUS = 25

DEFAULT_LEVELS = [
    # name, rank_order, minimum_points, maximum_points, benefits, description
    ("Bronze", 1, 0, 499,
     "Welcome rewards on every order.",
     "Everyone starts here."),
    ("Silver", 2, 500, 1499,
     "1x priority support, occasional bonus offers.",
     "Regular customers who order often."),
    ("Gold", 3, 1500, 2999,
     "Exclusive discounts, faster support, birthday rewards.",
     "Loyal customers with consistent activity."),
    ("Platinum", 4, 3000, 5999,
     "Free delivery credits, early access to deals.",
     "Top-tier frequent customers."),
    ("Diamond", 5, 6000, 9999,
     "Premium support line, higher cashback on wallet.",
     "Elite customers with very high lifetime spend."),
    ("Legends", 6, 10000, None,
     "All platform perks, dedicated support, maximum rewards.",
     "The highest achievable rank on QuickBite."),
]


def ensure_default_levels():
    """Idempotently seed the six default loyalty ranks if none exist yet.
    Admin can subsequently edit thresholds/benefits from the dashboard."""
    if LoyaltyLevel.query.count() > 0:
        return
    for name, order, mn, mx, benefits, desc in DEFAULT_LEVELS:
        db.session.add(LoyaltyLevel(
            name=name, rank_order=order, minimum_points=mn, maximum_points=mx,
            benefits=benefits, description=desc, is_active=True,
        ))
    db.session.commit()


def get_levels_ordered():
    return LoyaltyLevel.query.order_by(LoyaltyLevel.rank_order.asc()).all()


def rank_for_points(points: int) -> LoyaltyLevel:
    """Return the LoyaltyLevel whose [minimum_points, maximum_points] range
    contains `points`, using the currently configured (admin-editable)
    thresholds as the single source of truth."""
    levels = get_levels_ordered()
    if not levels:
        ensure_default_levels()
        levels = get_levels_ordered()

    match = None
    for lvl in levels:
        if not lvl.is_active:
            continue
        if points >= lvl.minimum_points and (lvl.maximum_points is None or points <= lvl.maximum_points):
            match = lvl
    if match:
        return match
    # Fallback: below the lowest active minimum -> lowest rank; above every
    # max -> highest rank. Keeps the system robust even mid-reconfiguration.
    active = [l for l in levels if l.is_active] or levels
    active_sorted = sorted(active, key=lambda l: l.rank_order)
    return active_sorted[0] if points < active_sorted[0].minimum_points else active_sorted[-1]


def get_or_create_loyalty(customer_id: int) -> CustomerLoyalty:
    loyalty = CustomerLoyalty.query.filter_by(customer_id=customer_id).first()
    if not loyalty:
        loyalty = CustomerLoyalty(customer_id=customer_id, points=0, lifetime_points=0, rank="Bronze")
        db.session.add(loyalty)
        db.session.commit()
    return loyalty


def recalc_rank(loyalty: CustomerLoyalty):
    level = rank_for_points(loyalty.points)
    loyalty.rank = level.name
    return level


def next_rank_info(loyalty: CustomerLoyalty):
    levels = get_levels_ordered()
    current = next((l for l in levels if l.name == loyalty.rank), None)
    if not current:
        return None, 0
    upper = [l for l in levels if l.rank_order > current.rank_order and l.is_active]
    if not upper:
        return None, 0  # already at the top rank
    nxt = min(upper, key=lambda l: l.rank_order)
    points_needed = max(nxt.minimum_points - loyalty.points, 0)
    return nxt, points_needed


def award_points_for_order(order: Order):
    """
    Awards loyalty points for a single completed (delivered) order.
    Idempotent: relies on the unique constraint on
    (reference_type, reference_id, transaction_type) in loyalty_transactions,
    so calling this twice for the same order never double-awards.
    Returns the LoyaltyTransaction created, or None if points were already
    awarded (or the order isn't eligible).
    """
    if order.order_status != "delivered":
        return None
    if order.payment_status != "paid":
        return None

    already = LoyaltyTransaction.query.filter_by(
        reference_type="order", reference_id=order.id, transaction_type="earn",
    ).first()
    if already:
        return None

    spend = float(order.total_amount)
    earned = int(round(spend / 100.0 * POINTS_PER_100_SPEND)) + COMPLETED_ORDER_BONUS

    loyalty = get_or_create_loyalty(order.customer_id)
    loyalty.points += earned
    loyalty.lifetime_points += earned
    loyalty.total_orders += 1
    loyalty.total_spending = float(loyalty.total_spending or 0) + spend
    recalc_rank(loyalty)

    txn = LoyaltyTransaction(
        customer_id=order.customer_id, points=earned, transaction_type="earn",
        reference_type="order", reference_id=order.id,
        description=f"Order #{order.id} completed (+{earned} pts: {COMPLETED_ORDER_BONUS} bonus + spend reward).",
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def reverse_points_for_order(order: Order, reason: str = "Order cancelled/refunded"):
    """
    Safely reverses a previously-awarded order reward (e.g. on
    cancellation/refund after the fact). Does nothing if no reward was ever
    given for this order, and never creates a duplicate reversal.
    """
    earn_txn = LoyaltyTransaction.query.filter_by(
        reference_type="order", reference_id=order.id, transaction_type="earn",
    ).first()
    if not earn_txn:
        return None

    already_reversed = LoyaltyTransaction.query.filter_by(
        reference_type="order", reference_id=order.id, transaction_type="reversal",
    ).first()
    if already_reversed:
        return None

    loyalty = get_or_create_loyalty(order.customer_id)
    loyalty.points = max(0, loyalty.points - earn_txn.points)
    loyalty.total_orders = max(0, loyalty.total_orders - 1)
    loyalty.total_spending = max(0.0, float(loyalty.total_spending or 0) - float(order.total_amount))
    recalc_rank(loyalty)

    txn = LoyaltyTransaction(
        customer_id=order.customer_id, points=-earn_txn.points, transaction_type="reversal",
        reference_type="order", reference_id=order.id, description=reason,
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def admin_adjust_points(customer_id: int, delta: int, reason: str, admin_id: int):
    """Manual admin point adjustment (positive to add, negative to remove).
    Always creates an audit-able loyalty_transactions row and recalculates rank."""
    loyalty = get_or_create_loyalty(customer_id)
    previous_points = loyalty.points
    loyalty.points = max(0, loyalty.points + delta)
    if delta > 0:
        loyalty.lifetime_points += delta
    level = recalc_rank(loyalty)

    txn = LoyaltyTransaction(
        customer_id=customer_id, points=delta,
        transaction_type="admin_add" if delta >= 0 else "admin_remove",
        reference_type="manual", reference_id=None,
        description=reason or "Manual adjustment by admin",
        admin_id=admin_id,
    )
    db.session.add(txn)
    db.session.commit()
    return loyalty, txn, previous_points, level


def recalculate_all_ranks():
    """Called after admin changes loyalty level thresholds -- every
    customer's rank label is recomputed against the new ranges."""
    count = 0
    for loyalty in CustomerLoyalty.query.all():
        old_rank = loyalty.rank
        recalc_rank(loyalty)
        if loyalty.rank != old_rank:
            count += 1
    db.session.commit()
    return count


def serialize_level(level: LoyaltyLevel):
    return {
        "id": level.id, "name": level.name, "rank_order": level.rank_order,
        "minimum_points": level.minimum_points, "maximum_points": level.maximum_points,
        "benefits": level.benefits, "description": level.description, "is_active": level.is_active,
    }


def serialize_loyalty_summary(loyalty: CustomerLoyalty):
    nxt, points_needed = next_rank_info(loyalty)
    current_level = LoyaltyLevel.query.filter_by(name=loyalty.rank).first()
    progress_pct = 100
    if nxt and current_level:
        span = nxt.minimum_points - current_level.minimum_points
        progress_pct = 100 if span <= 0 else min(100, max(0, round(
            (loyalty.points - current_level.minimum_points) / span * 100
        )))
    return {
        "rank": loyalty.rank,
        "points": loyalty.points,
        "lifetime_points": loyalty.lifetime_points,
        "total_orders": loyalty.total_orders,
        "total_spending": float(loyalty.total_spending or 0),
        "next_rank": nxt.name if nxt else None,
        "points_needed_for_next_rank": points_needed,
        "progress_percent": progress_pct,
        "current_level_benefits": current_level.benefits if current_level else None,
        "updated_at": loyalty.updated_at.isoformat() if loyalty.updated_at else None,
    }


def serialize_transaction(t: LoyaltyTransaction):
    return {
        "id": t.id, "points": t.points, "transaction_type": t.transaction_type,
        "reference_type": t.reference_type, "reference_id": t.reference_id,
        "description": t.description, "created_at": t.created_at.isoformat(),
    }
