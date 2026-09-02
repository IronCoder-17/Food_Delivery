"""
Food Streaks: an ENGAGEMENT streak, not a purchase requirement. Logging in,
finishing a GK Game round, or placing an order each count as one day's
activity -- calling record_activity() more than once on the same day is a
no-op, so nothing rewards spamming the same action repeatedly.

Milestone rewards are guarded by last_milestone_awarded so the exact same
milestone can never pay out twice, mirroring the idempotency pattern used
in loyalty_service.award_points_for_order().
"""
from datetime import date, timedelta

from backend.models.models import db, FoodStreak, LoyaltyTransaction
from backend.services import loyalty_service

# Every Nth consecutive day of ENGAGEMENT (not purchases) earns a milestone
# bonus, credited as loyalty points via the existing loyalty system.
MILESTONE_INTERVAL_DAYS = 5
MILESTONE_BONUS_POINTS = 50


def get_or_create(customer_id: int) -> FoodStreak:
    streak = FoodStreak.query.get(customer_id)
    if not streak:
        streak = FoodStreak(customer_id=customer_id, current_streak=0, best_streak=0, streak_points=0)
        db.session.add(streak)
        db.session.commit()
    return streak


def record_activity(customer_id: int, source: str = "activity"):
    """Advances (or starts) the customer's engagement streak for TODAY.
    Safe to call multiple times a day or from multiple trigger points
    (login, game, order) -- only the first call each day has any effect."""
    streak = get_or_create(customer_id)
    today = date.today()

    if streak.last_activity_date == today:
        return streak  # already counted today, no duplicate reward

    if streak.last_activity_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        # First-ever activity, or the streak was broken by a gap -- restart at 1,
        # and reset the milestone counter so a new streak can earn milestones again.
        streak.current_streak = 1
        streak.last_milestone_awarded = 0

    streak.last_activity_date = today
    streak.best_streak = max(streak.best_streak, streak.current_streak)

    milestones_reached = streak.current_streak // MILESTONE_INTERVAL_DAYS
    if milestones_reached > streak.last_milestone_awarded:
        new_milestones = milestones_reached - streak.last_milestone_awarded
        bonus = new_milestones * MILESTONE_BONUS_POINTS
        streak.streak_points += bonus
        streak.last_milestone_awarded = milestones_reached

        loyalty = loyalty_service.get_or_create_loyalty(customer_id)
        loyalty.points += bonus
        loyalty.lifetime_points += bonus
        loyalty_service.recalc_rank(loyalty)
        db.session.add(LoyaltyTransaction(
            customer_id=customer_id, points=bonus, transaction_type="earn",
            reference_type="streak", reference_id=milestones_reached,
            description=f"🔥 {streak.current_streak}-day engagement streak milestone (+{bonus} pts).",
        ))

    db.session.commit()
    return streak


def serialize(streak: FoodStreak):
    return {
        "current_streak": streak.current_streak,
        "best_streak": streak.best_streak,
        "streak_points": streak.streak_points,
        "last_activity_date": streak.last_activity_date.isoformat() if streak.last_activity_date else None,
        "days_to_next_milestone": (
            MILESTONE_INTERVAL_DAYS - (streak.current_streak % MILESTONE_INTERVAL_DAYS)
        ) % MILESTONE_INTERVAL_DAYS or MILESTONE_INTERVAL_DAYS,
    }
