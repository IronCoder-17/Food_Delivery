"""
Live Kitchen Load. A restaurant-set status (normal/busy/very_busy/
overloaded) plus a real extra-minutes estimate, shown to customers BEFORE
checkout and folded into the order's estimated delivery time -- never a
fabricated countdown.
"""
from backend.models.models import db, RestaurantKitchenStatus

VALID_STATUSES = {"normal", "busy", "very_busy", "overloaded"}

STATUS_LABELS = {
    "normal": "🟢 Kitchen Normal",
    "busy": "🟠 Kitchen Busy",
    "very_busy": "🟠 Kitchen Very Busy",
    "overloaded": "🔴 Temporarily Overloaded",
}


def get_status(restaurant_id):
    return RestaurantKitchenStatus.query.get(restaurant_id)


def get_or_default(restaurant_id):
    """Returns a serializable dict; restaurants with no row yet are
    'normal, +0 min' by default -- never an error or a guess."""
    row = get_status(restaurant_id)
    if not row:
        return {"restaurant_id": restaurant_id, "status": "normal", "extra_minutes": 0,
                "label": STATUS_LABELS["normal"]}
    return serialize(row)


def serialize(row: RestaurantKitchenStatus):
    return {
        "restaurant_id": row.restaurant_id,
        "status": row.status,
        "extra_minutes": row.extra_minutes,
        "label": STATUS_LABELS.get(row.status, row.status),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def set_status(restaurant_id, status, extra_minutes):
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    try:
        extra_minutes = int(extra_minutes)
        if extra_minutes < 0:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("extra_minutes must be a non-negative integer.")

    row = get_status(restaurant_id)
    if not row:
        row = RestaurantKitchenStatus(restaurant_id=restaurant_id)
        db.session.add(row)
    row.status = status
    row.extra_minutes = extra_minutes
    db.session.commit()
    return row


def extra_minutes_for(restaurant_id):
    row = get_status(restaurant_id)
    return row.extra_minutes if row else 0
