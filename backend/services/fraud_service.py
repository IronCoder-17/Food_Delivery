"""
Admin Fraud & Risk Center. This is a RULE-BASED detection system that flags
suspicious patterns for human review -- it never claims to prove fraud, and
it never auto-bans anyone. Restrictions only take effect when an admin
explicitly sets a flag's status to 'restricted', and that restriction is
enforced through the EXISTING Authority Management engine (not a second
system): it revokes customer.place_order so the person can't keep
transacting while under review.
"""
from datetime import datetime, timedelta
from collections import defaultdict

from backend.models.models import (
    db, Customer, Order, Payment, Referral, DisputeTicket, Address, FraudFlag,
)
from backend.services.authority_service import set_authority

LOOKBACK_DAYS = 30

# rule_key -> (threshold, weight_per_incident, human-readable template)
RULES = {
    "repeated_cod_cancellations": (3, 15, "{n} cancelled Cash-on-Delivery orders in the last {days} days."),
    "excessive_cancellations": (5, 10, "{n} cancelled orders (any payment method) in the last {days} days."),
    "frequent_failed_payments": (3, 12, "{n} failed payment attempts in the last {days} days."),
    "referral_abuse_pattern": (5, 20, "{n} completed referrals credited in the last {days} days -- unusually high volume."),
    "repeated_disputes": (3, 15, "{n} disputes opened in the last {days} days."),
    "shared_address_multi_account": (0, 25, "Shares an identical saved address with {n} other account(s)."),
}


def _upsert_flag(customer_id, rule, incident_count, reason):
    threshold, weight, _ = RULES[rule]
    flag = FraudFlag.query.filter_by(customer_id=customer_id, rule=rule).first()
    risk_score = min(100, incident_count * weight)
    if flag:
        # Never silently downgrade a flag an admin already reviewed into
        # 'review' again -- only refresh the evidence/count; status changes
        # remain an explicit admin action.
        flag.incident_count = incident_count
        flag.reason = reason
        flag.risk_score = risk_score
    else:
        db.session.add(FraudFlag(
            customer_id=customer_id, rule=rule, reason=reason,
            incident_count=incident_count, risk_score=risk_score, status="review",
        ))


def run_fraud_scan():
    """Re-scans recent activity platform-wide and upserts FraudFlag rows.
    Safe to call repeatedly (idempotent per customer+rule)."""
    since = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)

    # ---- repeated COD cancellations ----
    cod_cancels = defaultdict(int)
    for o in Order.query.filter(Order.order_status == "cancelled", Order.payment_method == "cod", Order.created_at >= since).all():
        cod_cancels[o.customer_id] += 1
    for cid, n in cod_cancels.items():
        if n >= RULES["repeated_cod_cancellations"][0]:
            _upsert_flag(cid, "repeated_cod_cancellations", n,
                         RULES["repeated_cod_cancellations"][2].format(n=n, days=LOOKBACK_DAYS))

    # ---- excessive cancellations (any method) ----
    all_cancels = defaultdict(int)
    for o in Order.query.filter(Order.order_status == "cancelled", Order.created_at >= since).all():
        all_cancels[o.customer_id] += 1
    for cid, n in all_cancels.items():
        if n >= RULES["excessive_cancellations"][0]:
            _upsert_flag(cid, "excessive_cancellations", n,
                         RULES["excessive_cancellations"][2].format(n=n, days=LOOKBACK_DAYS))

    # ---- frequent failed payments ----
    failed_by_customer = defaultdict(int)
    failed_payments = (
        db.session.query(Payment, Order.customer_id)
        .join(Order, Payment.order_id == Order.id)
        .filter(Payment.status == "failed", Payment.created_at >= since)
        .all()
    )
    for _, customer_id in failed_payments:
        failed_by_customer[customer_id] += 1
    for cid, n in failed_by_customer.items():
        if n >= RULES["frequent_failed_payments"][0]:
            _upsert_flag(cid, "frequent_failed_payments", n,
                         RULES["frequent_failed_payments"][2].format(n=n, days=LOOKBACK_DAYS))

    # ---- referral abuse pattern (unusually many completed referrals fast) ----
    referral_counts = defaultdict(int)
    for r in Referral.query.filter(Referral.status == "completed", Referral.completed_at >= since).all():
        referral_counts[r.referrer_customer_id] += 1
    for cid, n in referral_counts.items():
        if n >= RULES["referral_abuse_pattern"][0]:
            _upsert_flag(cid, "referral_abuse_pattern", n,
                         RULES["referral_abuse_pattern"][2].format(n=n, days=LOOKBACK_DAYS))

    # ---- repeated disputes ----
    dispute_counts = defaultdict(int)
    for d in DisputeTicket.query.filter(DisputeTicket.created_at >= since).all():
        dispute_counts[d.customer_id] += 1
    for cid, n in dispute_counts.items():
        if n >= RULES["repeated_disputes"][0]:
            _upsert_flag(cid, "repeated_disputes", n,
                         RULES["repeated_disputes"][2].format(n=n, days=LOOKBACK_DAYS))

    # ---- multiple accounts sharing an identical saved address ----
    address_groups = defaultdict(set)
    for a in Address.query.all():
        key = a.address.strip().lower()
        address_groups[key].add(a.customer_id)
    for key, customer_ids in address_groups.items():
        if len(customer_ids) < 2:
            continue
        for cid in customer_ids:
            others = len(customer_ids) - 1
            _upsert_flag(cid, "shared_address_multi_account", others,
                         RULES["shared_address_multi_account"][2].format(n=others))

    db.session.commit()


def set_flag_status(flag: FraudFlag, new_status, admin_id):
    """Transitions a flag's status. Only 'restricted' actually changes
    account access, and it does so via the real Authority Management
    engine -- never a parallel ban system."""
    if new_status not in ("review", "warning", "restricted", "cleared"):
        raise ValueError("Invalid status.")

    was_restricted = flag.status == "restricted"
    flag.status = new_status
    flag.reviewed_by_admin_id = admin_id

    if new_status == "restricted" and not was_restricted:
        set_authority(flag.customer_id, "customer", "customer.place_order", False, admin_id,
                       reason=f"Restricted due to fraud flag: {flag.rule}")
    elif was_restricted and new_status != "restricted":
        # Only lift the restriction if no OTHER active restricted flag remains for this customer.
        other_restricted = FraudFlag.query.filter(
            FraudFlag.customer_id == flag.customer_id, FraudFlag.id != flag.id, FraudFlag.status == "restricted",
        ).first()
        if not other_restricted:
            set_authority(flag.customer_id, "customer", "customer.place_order", True, admin_id,
                          reason=f"Restriction lifted: fraud flag '{flag.rule}' set to {new_status}")

    db.session.commit()


def serialize_flag(f: FraudFlag):
    return {
        "id": f.id,
        "customer_id": f.customer_id,
        "customer_name": f"{f.customer.first_name} {f.customer.last_name}" if f.customer else None,
        "rule": f.rule,
        "reason": f.reason,
        "incident_count": f.incident_count,
        "risk_score": f.risk_score,
        "status": f.status,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }
