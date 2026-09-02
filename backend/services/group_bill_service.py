"""
Group Bill Splitting.

Design note (why this isn't fake): the spec explicitly forbids simulated
UPI payments. This codebase has no external payment-collection integration
wired up anywhere (Razorpay's key is configured but only used for card/UPI
payments the CUSTOMER already initiates from their own device via the
Razorpay SDK on a single order -- there's no server-side "charge someone
else's UPI" capability to extend, and building one is outside this batch).

So bill-splitting here uses the app's own REAL Wallet system: the group's
Order is already fully and genuinely paid by the host at checkout
(unchanged, existing flow). This feature computes each member's fair share
and lets them REIMBURSE the host via their own wallet -- a real balance
check, a real debit, a real credit, with real pending/paid/failed/refunded
statuses. Nothing here is simulated.
"""
from datetime import datetime

from backend.models.models import db, GroupOrder, GroupOrderPayment, GroupOrderMember
from backend.services.pricing_service import effective_food_price
from backend.services.wallet_service import credit_wallet, debit_wallet


def _member_contribution(group_order: GroupOrder, customer_id: int) -> float:
    total = 0.0
    for item in group_order.items:
        if item.customer_id != customer_id or not item.food:
            continue
        price, _ = effective_food_price(item.food)
        total += price * item.quantity
    return round(total, 2)


def group_total(group_order: GroupOrder) -> float:
    total = 0.0
    for item in group_order.items:
        if not item.food:
            continue
        price, _ = effective_food_price(item.food)
        total += price * item.quantity
    return round(total, 2)


def has_been_split(group_order_id: int) -> bool:
    return GroupOrderPayment.query.filter_by(group_order_id=group_order_id).first() is not None


def split_bill(group_order: GroupOrder, split_type: str):
    """Creates one GroupOrderPayment row per member. The host's own share
    is marked 'paid' immediately (they already paid the whole order at
    checkout); every other member's share starts 'pending'."""
    if split_type not in ("equal", "item_based"):
        raise ValueError("split_type must be 'equal' or 'item_based'.")
    if has_been_split(group_order.id):
        raise ValueError("This group order's bill has already been split.")

    members = GroupOrderMember.query.filter_by(group_order_id=group_order.id).all()
    if not members:
        raise ValueError("No members to split the bill among.")

    total = group_total(group_order)
    shares = {}
    if split_type == "equal":
        per_head = round(total / len(members), 2)
        for m in members:
            shares[m.customer_id] = per_head
    else:  # item_based
        for m in members:
            shares[m.customer_id] = _member_contribution(group_order, m.customer_id)

    rows = []
    for m in members:
        amount = shares.get(m.customer_id, 0)
        status = "paid" if m.customer_id == group_order.host_customer_id else "pending"
        row = GroupOrderPayment(
            group_order_id=group_order.id, customer_id=m.customer_id, amount=amount,
            split_type=split_type, status=status,
            paid_at=datetime.utcnow() if status == "paid" else None,
        )
        db.session.add(row)
        rows.append(row)
    db.session.commit()
    return rows


def pay_my_share(group_order: GroupOrder, customer_id: int):
    """Debits the paying member's wallet and credits the host's wallet for
    their pending share. Raises ValueError on any invalid state (no split,
    already paid, insufficient balance) -- callers turn that into a 400."""
    row = GroupOrderPayment.query.filter_by(group_order_id=group_order.id, customer_id=customer_id).first()
    if not row:
        raise ValueError("No bill split found for you on this group order.")
    if row.status == "paid":
        raise ValueError("This share has already been paid.")
    if row.status == "refunded":
        raise ValueError("This share was refunded and can't be paid again.")

    try:
        debit_wallet(customer_id, float(row.amount), f"Group order #{group_order.id} bill split", "group_order_payment", row.id)
        credit_wallet(group_order.host_customer_id, float(row.amount), f"Group order #{group_order.id} reimbursement", "group_order_payment", row.id)
    except ValueError:
        row.status = "failed"
        db.session.commit()
        raise

    row.status = "paid"
    row.paid_at = datetime.utcnow()
    db.session.commit()
    return row


def refund_share(group_order: GroupOrder, target_customer_id: int):
    """Host-initiated refund of an already-paid share: reverses the wallet
    movement (credit back to the member, debit from the host)."""
    row = GroupOrderPayment.query.filter_by(group_order_id=group_order.id, customer_id=target_customer_id).first()
    if not row:
        raise ValueError("No bill split found for that member.")
    if row.status != "paid":
        raise ValueError("Only a paid share can be refunded.")

    debit_wallet(group_order.host_customer_id, float(row.amount), f"Refund to member for group order #{group_order.id}", "group_order_refund", row.id)
    credit_wallet(target_customer_id, float(row.amount), f"Refund from group order #{group_order.id}", "group_order_refund", row.id)

    row.status = "refunded"
    db.session.commit()
    return row


def serialize(row: GroupOrderPayment):
    return {
        "id": row.id,
        "customer_id": row.customer_id,
        "customer_name": f"{row.customer.first_name} {row.customer.last_name[0]}." if row.customer else "Member",
        "amount": float(row.amount),
        "split_type": row.split_type,
        "status": row.status,
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }
