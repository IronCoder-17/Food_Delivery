"""
QuickBite Pass -- a delivery-fee subscription for customers. Every
eligibility check here re-reads the database at call time; nothing about
eligibility or usage counts is ever trusted from the client.
"""
from datetime import datetime, timedelta

from backend.models.models import db, QuickBitePass, PassPlan, PassPlanRestaurant, DeliveryBenefitUsage


def get_active_pass(customer_id):
    """Returns the customer's active pass, lazily expiring it first if its
    validity window has actually elapsed."""
    passes = QuickBitePass.query.filter_by(customer_id=customer_id, status="active").all()
    for p in passes:
        if p.expires_at <= datetime.utcnow():
            p.status = "expired"
    db.session.commit()
    return QuickBitePass.query.filter_by(customer_id=customer_id, status="active").first()


def _sync_period(pass_: QuickBitePass):
    """Free-delivery counts reset every 30-day period from the pass's
    start date (not calendar months, so a mid-month subscription doesn't
    get a truncated first period)."""
    period_index = (datetime.utcnow() - pass_.started_at).days // 30
    if period_index != pass_.current_period_index:
        pass_.current_period_index = period_index
        pass_.deliveries_used_in_period = 0


def get_eligible_benefit(customer_id, restaurant_id, subtotal):
    """Returns the active QuickBitePass if it can cover this order's
    delivery fee right now, else None. Does not mutate/consume anything --
    call apply_benefit() only after the order actually exists."""
    pass_ = get_active_pass(customer_id)
    if not pass_:
        return None

    plan = pass_.plan
    if not plan or not plan.is_active:
        return None

    if plan.eligible_restaurants:
        eligible_ids = {r.restaurant_id for r in plan.eligible_restaurants}
        if restaurant_id not in eligible_ids:
            return None

    if subtotal < float(plan.min_order_amount or 0):
        return None

    _sync_period(pass_)
    db.session.commit()

    if pass_.deliveries_used_in_period >= plan.max_free_deliveries_per_period:
        return None

    return pass_


def apply_benefit(pass_: QuickBitePass, order_id, customer_id, delivery_fee_waived):
    """Call once the Order row exists. Idempotent per order via the unique
    constraint on DeliveryBenefitUsage.order_id."""
    if DeliveryBenefitUsage.query.filter_by(order_id=order_id).first():
        return  # already applied -- never double-count
    db.session.add(DeliveryBenefitUsage(
        order_id=order_id, customer_id=customer_id, pass_id=pass_.id, discount_amount=delivery_fee_waived,
    ))
    pass_.deliveries_used_in_period += 1
    db.session.commit()


def subscribe(customer, plan: PassPlan):
    """Creates a new QuickBitePass for the customer, cancelling any
    existing active pass first (no stacking multiple active passes)."""
    existing = QuickBitePass.query.filter_by(customer_id=customer.id, status="active").first()
    if existing:
        existing.status = "cancelled"

    pass_ = QuickBitePass(
        customer_id=customer.id, plan_id=plan.id,
        started_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(days=plan.duration_days),
        status="active",
    )
    db.session.add(pass_)
    db.session.commit()
    return pass_


def serialize_pass(p: QuickBitePass):
    return {
        "id": p.id,
        "plan_id": p.plan_id,
        "plan_name": p.plan.name if p.plan else None,
        "started_at": p.started_at.isoformat() if p.started_at else None,
        "expires_at": p.expires_at.isoformat() if p.expires_at else None,
        "status": p.status,
        "is_currently_active": p.is_currently_active(),
        "max_free_deliveries_per_period": p.plan.max_free_deliveries_per_period if p.plan else None,
        "deliveries_used_in_period": p.deliveries_used_in_period,
    }


def serialize_plan(plan: PassPlan):
    return {
        "id": plan.id,
        "name": plan.name,
        "price": float(plan.price),
        "duration_days": plan.duration_days,
        "min_order_amount": float(plan.min_order_amount or 0),
        "max_free_deliveries_per_period": plan.max_free_deliveries_per_period,
        "is_active": bool(plan.is_active),
        "eligible_restaurant_ids": [r.restaurant_id for r in plan.eligible_restaurants],
    }
