"""
Restaurant Subscription Plans. Integrates with the EXISTING Authority
Management engine (no second permission system): the permissions a plan
grants are applied as real UserAuthority overrides the moment a subscription
is activated, and are automatically reverted the moment it expires or is
cancelled -- so restaurant access changes immediately, exactly as the spec
requires, and the backend (not just the UI) enforces it because every
gated route already checks require_permission()/has_permission().

Note on billing: this app has no restaurant-side payment/wallet
infrastructure (Wallet is customer-only). Rather than fabricate a fake
"payment succeeded" step for restaurants, subscription activation is an
explicit admin action (the restaurant requests a plan, an admin activates
it once payment is collected through whatever real-world channel the
business uses) -- the same pattern this app already uses for restaurant
registration approval.
"""
from datetime import datetime, timedelta

from backend.models.models import db, RestaurantSubscription, SubscriptionPlan
from backend.services.authority_service import set_authority


def _revoke_plan_permissions(subscription: RestaurantSubscription, admin_id, reason):
    plan = subscription.plan
    if not plan:
        return
    for key in plan.permission_list():
        try:
            set_authority(subscription.restaurant_id, "restaurant", key, False, admin_id, reason=reason)
        except ValueError:
            pass  # permission key no longer exists in the catalog -- skip rather than fail the whole revert


def _grant_plan_permissions(subscription: RestaurantSubscription, admin_id, reason):
    plan = subscription.plan
    if not plan:
        return
    for key in plan.permission_list():
        try:
            set_authority(subscription.restaurant_id, "restaurant", key, True, admin_id, reason=reason)
        except ValueError:
            pass


def sync_expiry(subscription: RestaurantSubscription):
    """Lazily expires a subscription (and reverts its granted permissions)
    if its window has passed. Call before showing subscription status
    anywhere."""
    if subscription.status == "active" and subscription.expires_at <= datetime.utcnow():
        _revoke_plan_permissions(subscription, admin_id=None, reason="system: subscription expired")
        subscription.status = "expired"
        db.session.commit()


def request_plan(restaurant_id, plan: SubscriptionPlan):
    sub = RestaurantSubscription(
        restaurant_id=restaurant_id, plan_id=plan.id, status="pending",
        expires_at=datetime.utcnow() + timedelta(days=plan.duration_days),  # placeholder until activated
    )
    db.session.add(sub)
    db.session.commit()
    return sub


def activate(subscription: RestaurantSubscription, admin_id):
    # Cancel any other active subscription for this restaurant first --
    # a restaurant has exactly one active plan at a time.
    others = RestaurantSubscription.query.filter(
        RestaurantSubscription.restaurant_id == subscription.restaurant_id,
        RestaurantSubscription.status == "active",
        RestaurantSubscription.id != subscription.id,
    ).all()
    for other in others:
        _revoke_plan_permissions(other, admin_id, reason=f"Replaced by subscription #{subscription.id}")
        other.status = "cancelled"

    subscription.status = "active"
    subscription.started_at = datetime.utcnow()
    subscription.expires_at = datetime.utcnow() + timedelta(days=subscription.plan.duration_days)
    subscription.activated_by_admin_id = admin_id
    _grant_plan_permissions(subscription, admin_id, reason=f"Activated subscription to '{subscription.plan.name}'")
    db.session.commit()
    return subscription


def cancel(subscription: RestaurantSubscription, admin_id):
    _revoke_plan_permissions(subscription, admin_id, reason="Subscription cancelled by admin")
    subscription.status = "cancelled"
    db.session.commit()
    return subscription


def serialize_subscription(sub: RestaurantSubscription):
    return {
        "id": sub.id,
        "restaurant_id": sub.restaurant_id,
        "restaurant_name": sub.restaurant.restaurant_name if sub.restaurant else None,
        "plan_id": sub.plan_id,
        "plan_name": sub.plan.name if sub.plan else None,
        "status": sub.status,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        "requested_at": sub.requested_at.isoformat() if sub.requested_at else None,
    }


def serialize_plan(plan: SubscriptionPlan):
    return {
        "id": plan.id,
        "name": plan.name,
        "price": float(plan.price),
        "duration_days": plan.duration_days,
        "description": plan.description,
        "granted_permissions": plan.permission_list(),
        "is_active": bool(plan.is_active),
    }
