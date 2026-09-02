from datetime import datetime

from backend.models.models import db, DisputeTicket, DisputeEvent, Order
from backend.services.wallet_service import credit_wallet

VALID_REASONS = {"missing_item", "wrong_item", "damaged_item", "payment_issue", "delivery_issue", "other"}
TERMINAL_STATUSES = {"resolved", "rejected"}


def create_dispute(customer, order: Order, reason, description, evidence_url):
    if order.order_status != "delivered":
        raise ValueError("You can only open a dispute for a delivered order.")

    existing_open = DisputeTicket.query.filter(
        DisputeTicket.order_id == order.id, DisputeTicket.customer_id == customer.id,
        DisputeTicket.status.notin_(TERMINAL_STATUSES),
    ).first()
    if existing_open:
        raise ValueError("You already have an open dispute for this order.")

    ticket = DisputeTicket(
        order_id=order.id, customer_id=customer.id, restaurant_id=order.restaurant_id,
        reason=reason, description=description, evidence_url=evidence_url, status="open",
    )
    db.session.add(ticket)
    db.session.flush()
    db.session.add(DisputeEvent(
        dispute_id=ticket.id, actor_type="customer", actor_id=customer.id,
        event_type="created", note=f"Dispute opened: {reason}",
    ))
    db.session.commit()
    return ticket


def update_status(ticket: DisputeTicket, new_status, admin_id, note=None):
    valid_statuses = {"open", "under_review", "waiting_for_restaurant", "resolved", "rejected"}
    if new_status not in valid_statuses:
        raise ValueError("Invalid status.")

    previous = ticket.status
    ticket.status = new_status
    db.session.add(DisputeEvent(
        dispute_id=ticket.id, actor_type="admin", actor_id=admin_id,
        event_type="status_change", note=note or f"Status changed from '{previous}' to '{new_status}'.",
    ))
    db.session.commit()


def resolve_with_refund(ticket: DisputeTicket, admin_id, resolution_note, refund_amount):
    if refund_amount is not None and refund_amount > 0:
        credit_wallet(
            ticket.customer_id, float(refund_amount),
            f"Dispute #{ticket.id} resolution refund", "dispute", ticket.id,
        )
        ticket.refund_amount = refund_amount

    ticket.status = "resolved"
    ticket.resolution_note = resolution_note
    ticket.resolved_by_admin_id = admin_id
    db.session.add(DisputeEvent(
        dispute_id=ticket.id, actor_type="admin", actor_id=admin_id, event_type="resolution",
        note=f"Resolved. Refund: ₹{refund_amount or 0}. Note: {resolution_note or '(none)'}",
    ))
    db.session.commit()


def serialize_dispute(d: DisputeTicket, include_events=False):
    data = {
        "id": d.id,
        "order_id": d.order_id,
        "customer_id": d.customer_id,
        "customer_name": f"{d.customer.first_name} {d.customer.last_name}" if d.customer else None,
        "restaurant_id": d.restaurant_id,
        "restaurant_name": d.restaurant.restaurant_name if d.restaurant else None,
        "reason": d.reason,
        "description": d.description,
        "evidence_url": d.evidence_url,
        "status": d.status,
        "resolution_note": d.resolution_note,
        "refund_amount": float(d.refund_amount) if d.refund_amount is not None else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }
    if include_events:
        data["events"] = [{
            "actor_type": e.actor_type, "event_type": e.event_type, "note": e.note,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in d.events]
    return data
