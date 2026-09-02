"""
Referral System. Integrates with the existing Loyalty engine (never a
second, parallel points system) and relies on the same idempotency pattern
loyalty_service already uses -- a unique (reference_type, reference_id,
transaction_type) constraint on loyalty_transactions -- to guarantee a
referral can never pay out twice, even if this function is called
repeatedly (e.g. an order re-checked by multiple code paths).

Anti-abuse measures actually enforced here:
  * A customer can be referred at most once, ever (Referral.referred_customer_id
    is UNIQUE) -- so switching codes or re-registering with a different
    referral code after the first one can't stack rewards.
  * Self-referral is structurally impossible: the referred customer doesn't
    exist until after registration, and mobile_number/email are already
    unique across accounts, so a code can't resolve to the same person
    using the same identity twice. We additionally guard referrer.id ==
    referred.id defensively even though it can't occur through this flow.
  * The reward only fires once the referred customer's FIRST delivered +
    paid order completes -- not on signup alone -- so a referral can't be
    farmed by creating an account and never actually transacting.
"""
import random
import re
from datetime import datetime

from backend.models.models import db, Customer, Referral, ReferralConfig, LoyaltyTransaction, Order
from backend.services import loyalty_service


def get_or_create_referral_config() -> ReferralConfig:
    cfg = ReferralConfig.query.first()
    if not cfg:
        cfg = ReferralConfig(referrer_points=100, referred_points=50, is_active=True)
        db.session.add(cfg)
        db.session.commit()
    return cfg


def get_or_create_referral_code(customer: Customer) -> str:
    if customer.referral_code:
        return customer.referral_code

    name_part = re.sub(r"[^A-Z]", "", customer.first_name.upper())[:8] or "USER"
    for _ in range(30):
        code = f"QB-{name_part}-{random.randint(1000, 9999)}"
        if not Customer.query.filter_by(referral_code=code).first():
            customer.referral_code = code
            db.session.commit()
            return code
    raise RuntimeError("Could not generate a unique referral code.")


def apply_referral_code_at_registration(new_customer: Customer, code: str):
    """Called right after `new_customer` is created & flushed (has an id).
    Returns a dict describing the outcome; never raises for a bad code --
    an invalid/expired code should not block registration, just not link
    a referral. The caller decides whether to surface `warning` to the
    person."""
    if not code or not code.strip():
        return {"linked": False}

    code = code.strip().upper()
    referrer = Customer.query.filter_by(referral_code=code).first()
    if not referrer:
        return {"linked": False, "warning": "Referral code not recognized -- continuing without it."}
    if referrer.id == new_customer.id:
        return {"linked": False, "warning": "You cannot refer yourself."}

    if Referral.query.filter_by(referred_customer_id=new_customer.id).first():
        return {"linked": False, "warning": "A referral has already been recorded for this account."}

    referral = Referral(
        referrer_customer_id=referrer.id, referred_customer_id=new_customer.id,
        referral_code_used=code, status="pending",
    )
    db.session.add(referral)
    db.session.commit()
    return {"linked": True, "referral_id": referral.id}


def process_referral_if_qualified(order: Order):
    """Call whenever an order transitions to delivered+paid. No-ops unless
    `order.customer_id` was referred, has a pending referral, and this is
    genuinely their first-ever delivered+paid order."""
    if order.order_status != "delivered" or order.payment_status != "paid":
        return

    referral = Referral.query.filter_by(referred_customer_id=order.customer_id, status="pending").first()
    if not referral:
        return

    prior_qualifying_orders = Order.query.filter(
        Order.customer_id == order.customer_id, Order.order_status == "delivered",
        Order.payment_status == "paid", Order.id != order.id,
    ).count()
    if prior_qualifying_orders > 0:
        return  # referral only rewards the customer's FIRST completed order

    cfg = get_or_create_referral_config()
    if not cfg.is_active:
        return

    # Award referrer -- idempotent via the unique constraint on
    # (reference_type, reference_id, transaction_type) in loyalty_transactions.
    if not LoyaltyTransaction.query.filter_by(
        reference_type="referral_referrer", reference_id=referral.id, transaction_type="earn"
    ).first():
        referrer_loyalty = loyalty_service.get_or_create_loyalty(referral.referrer_customer_id)
        referrer_loyalty.points += cfg.referrer_points
        referrer_loyalty.lifetime_points += cfg.referrer_points
        loyalty_service.recalc_rank(referrer_loyalty)
        db.session.add(LoyaltyTransaction(
            customer_id=referral.referrer_customer_id, points=cfg.referrer_points, transaction_type="earn",
            reference_type="referral_referrer", reference_id=referral.id,
            description=f"Referral reward: your invite completed their first order (Order #{order.id}).",
        ))

    if not LoyaltyTransaction.query.filter_by(
        reference_type="referral_referred", reference_id=referral.id, transaction_type="earn"
    ).first():
        referred_loyalty = loyalty_service.get_or_create_loyalty(referral.referred_customer_id)
        referred_loyalty.points += cfg.referred_points
        referred_loyalty.lifetime_points += cfg.referred_points
        loyalty_service.recalc_rank(referred_loyalty)
        db.session.add(LoyaltyTransaction(
            customer_id=referral.referred_customer_id, points=cfg.referred_points, transaction_type="earn",
            reference_type="referral_referred", reference_id=referral.id,
            description=f"Welcome bonus: your first order (Order #{order.id}) qualified your referral.",
        ))

    referral.status = "completed"
    referral.completed_at = datetime.utcnow()
    referral.qualifying_order_id = order.id
    db.session.commit()


def serialize_referral(r: Referral, viewer_customer_id):
    return {
        "id": r.id,
        "referred_name": f"{r.referred.first_name} {r.referred.last_name[0]}." if r.referred else "Unknown",
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "qualifying_order_id": r.qualifying_order_id,
    }
