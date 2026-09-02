"""
Promotion A/B Testing. Only one experiment runs at a time (kept simple and
unambiguous -- combining multiple simultaneous discounts on one order would
make the resulting conversion/revenue numbers hard to attribute correctly).
Assignment is a controlled deterministic method (customer_id parity) rather
than fresh randomness each time, so a customer always sees the same variant
for the lifetime of the experiment -- required for a valid A/B comparison.
"""
from backend.models.models import db, PromotionExperiment, PromotionAssignment, Order
from sqlalchemy import func


def get_running_experiment():
    experiments = PromotionExperiment.query.filter_by(status="running").all()
    for e in experiments:
        if e.is_currently_running():
            return e
    return None


def get_or_create_assignment(experiment: PromotionExperiment, customer_id: int) -> PromotionAssignment:
    existing = PromotionAssignment.query.filter_by(experiment_id=experiment.id, customer_id=customer_id).first()
    if existing:
        return existing
    variant = "A" if customer_id % 2 == 0 else "B"
    assignment = PromotionAssignment(experiment_id=experiment.id, customer_id=customer_id, variant=variant)
    db.session.add(assignment)
    db.session.commit()
    return assignment


def get_order_discount(customer_id: int, subtotal: float):
    """Returns (discount_amount, assignment_id_or_None). Called at
    checkout -- never trusts any discount value from the client."""
    experiment = get_running_experiment()
    if not experiment:
        return 0.0, None

    assignment = get_or_create_assignment(experiment, customer_id)
    discount_percent = float(experiment.discount_percent_a if assignment.variant == "A" else experiment.discount_percent_b)
    if discount_percent <= 0:
        return 0.0, assignment.id
    discount = round(subtotal * discount_percent / 100, 2)
    return discount, assignment.id


def experiment_stats(experiment: PromotionExperiment):
    stats = {}
    for variant in ("A", "B"):
        assignment_ids = [
            a.id for a in PromotionAssignment.query.filter_by(experiment_id=experiment.id, variant=variant).all()
        ]
        exposed = len(assignment_ids)
        if assignment_ids:
            orders = Order.query.filter(Order.promotion_assignment_id.in_(assignment_ids)).all()
        else:
            orders = []
        paid_orders = [o for o in orders if o.payment_status == "paid"]
        revenue = sum(float(o.total_amount) for o in paid_orders)
        converted_customers = len({o.customer_id for o in paid_orders})
        stats[variant] = {
            "label": experiment.variant_a_label if variant == "A" else experiment.variant_b_label,
            "discount_percent": float(experiment.discount_percent_a if variant == "A" else experiment.discount_percent_b),
            "users_exposed": exposed,
            "orders": len(paid_orders),
            "revenue": round(revenue, 2),
            "conversion_rate": round(converted_customers / exposed * 100, 2) if exposed else 0,
            "average_order_value": round(revenue / len(paid_orders), 2) if paid_orders else 0,
        }
    return stats


def serialize_experiment(e: PromotionExperiment, include_stats=False):
    data = {
        "id": e.id,
        "name": e.name,
        "variant_a_label": e.variant_a_label,
        "variant_b_label": e.variant_b_label,
        "discount_percent_a": float(e.discount_percent_a),
        "discount_percent_b": float(e.discount_percent_b),
        "status": e.status,
        "start_date": e.start_date.isoformat() if e.start_date else None,
        "end_date": e.end_date.isoformat() if e.end_date else None,
        "is_currently_running": e.is_currently_running(),
    }
    if include_stats:
        data["stats"] = experiment_stats(e)
    return data
