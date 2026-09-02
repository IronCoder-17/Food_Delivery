"""
Peak-Hour Analytics and Order Heatmap. Extends the existing Admin
analytics area with real, SQL-aggregated data -- every number here comes
from actual Order/OrderItem rows, filtered by the requested date range.
"""
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from sqlalchemy import extract, func

from backend.models.models import db, Order, OrderItem, City
from backend.middleware.auth_middleware import token_required

admin_analytics_bp = Blueprint("admin_analytics", __name__, url_prefix="/api/admin/analytics")


def _resolve_range():
    """Returns (start, end) datetimes based on ?range=today|7d|30d|custom
    (&start=&end= for custom, ISO 8601)."""
    range_key = request.args.get("range", "7d")
    now = datetime.utcnow()
    if range_key == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    if range_key == "30d":
        return now - timedelta(days=30), now
    if range_key == "custom":
        try:
            start = datetime.fromisoformat(request.args.get("start"))
            end = datetime.fromisoformat(request.args.get("end"))
            return start, end
        except (TypeError, ValueError):
            return now - timedelta(days=7), now
    return now - timedelta(days=7), now  # default 7d


@admin_analytics_bp.route("/peak-hours", methods=["GET"])
@token_required(["admin"])
def peak_hour_analytics():
    start, end = _resolve_range()
    base = Order.query.filter(Order.created_at >= start, Order.created_at <= end, Order.payment_status == "paid")

    # ---- Orders & revenue by hour of day (0-23) ----
    hour_rows = (
        db.session.query(extract("hour", Order.created_at).label("h"), func.count(Order.id), func.sum(Order.total_amount))
        .filter(Order.created_at >= start, Order.created_at <= end, Order.payment_status == "paid")
        .group_by("h").all()
    )
    by_hour = {int(h): (int(c), float(rev or 0)) for h, c, rev in hour_rows}
    orders_by_hour = [{"hour": h, "orders": by_hour.get(h, (0, 0))[0]} for h in range(24)]
    revenue_by_hour = [{"hour": h, "revenue": round(by_hour.get(h, (0, 0))[1], 2)} for h in range(24)]

    # ---- Orders by day within range ----
    day_rows = (
        db.session.query(func.date(Order.created_at).label("d"), func.count(Order.id))
        .filter(Order.created_at >= start, Order.created_at <= end, Order.payment_status == "paid")
        .group_by("d").order_by("d").all()
    )
    orders_by_day = [{"date": str(d), "orders": int(c)} for d, c in day_rows]

    # ---- Peak hour(s): the hour(s) with the maximum order count ----
    max_orders = max((x["orders"] for x in orders_by_hour), default=0)
    peak_hours = [x["hour"] for x in orders_by_hour if x["orders"] == max_orders and max_orders > 0]

    # ---- Popular foods / restaurants during peak hour(s) ----
    popular_foods, popular_restaurants = [], []
    if peak_hours:
        peak_items = (
            db.session.query(OrderItem.food_name, func.sum(OrderItem.quantity).label("qty"))
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.created_at >= start, Order.created_at <= end, Order.payment_status == "paid",
                    extract("hour", Order.created_at).in_(peak_hours))
            .group_by(OrderItem.food_name).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()
        )
        popular_foods = [{"food_name": n, "quantity": int(q)} for n, q in peak_items]

        peak_restaurants = (
            db.session.query(Order.restaurant_id, func.count(Order.id).label("cnt"))
            .filter(Order.created_at >= start, Order.created_at <= end, Order.payment_status == "paid",
                    extract("hour", Order.created_at).in_(peak_hours))
            .group_by(Order.restaurant_id).order_by(func.count(Order.id).desc()).limit(10).all()
        )
        from backend.models.models import Restaurant
        popular_restaurants = [{
            "restaurant_id": rid, "restaurant_name": (Restaurant.query.get(rid).restaurant_name if Restaurant.query.get(rid) else None),
            "orders": int(cnt),
        } for rid, cnt in peak_restaurants]

    total_orders = base.count()
    total_revenue = float(db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= start, Order.created_at <= end, Order.payment_status == "paid").scalar() or 0)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0

    return jsonify({
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "orders_by_hour": orders_by_hour,
        "revenue_by_hour": revenue_by_hour,
        "orders_by_day": orders_by_day,
        "peak_hours": peak_hours,
        "popular_foods_at_peak": popular_foods,
        "popular_restaurants_at_peak": popular_restaurants,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": avg_order_value,
    }), 200


@admin_analytics_bp.route("/heatmap", methods=["GET"])
@token_required(["admin"])
def order_heatmap():
    """Aggregated order density by city and pincode -- NEVER individual
    addresses/pins. Only orders that snapshotted structured location data
    (i.e. checked out with a saved Address) are included; this is real
    coverage, not an estimate for the rest."""
    start, end = _resolve_range()

    city_rows = (
        db.session.query(
            Order.delivery_city_id, func.count(Order.id).label("cnt"),
            func.avg(Order.delivery_latitude).label("lat"), func.avg(Order.delivery_longitude).label("lng"),
        )
        .filter(Order.created_at >= start, Order.created_at <= end, Order.delivery_city_id.isnot(None))
        .group_by(Order.delivery_city_id).order_by(func.count(Order.id).desc()).all()
    )
    cities = []
    for city_id, cnt, lat, lng in city_rows:
        city = City.query.get(city_id)
        cities.append({
            "city_id": city_id, "city_name": city.name if city else None, "order_count": int(cnt),
            "latitude": float(lat) if lat is not None else None, "longitude": float(lng) if lng is not None else None,
        })

    pincode_rows = (
        db.session.query(Order.delivery_pincode, func.count(Order.id).label("cnt"))
        .filter(Order.created_at >= start, Order.created_at <= end, Order.delivery_pincode.isnot(None))
        .group_by(Order.delivery_pincode).order_by(func.count(Order.id).desc()).limit(50).all()
    )
    pincodes = [{"pincode": p, "order_count": int(c)} for p, c in pincode_rows]

    total_with_location = sum(c["order_count"] for c in cities)
    total_orders_in_range = Order.query.filter(Order.created_at >= start, Order.created_at <= end).count()

    return jsonify({
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "cities": cities,
        "pincodes": pincodes,
        "coverage_note": (
            f"{total_with_location} of {total_orders_in_range} orders in range have structured location data "
            "(orders placed with a saved address). Orders with a freely-typed address aren't geocoded or guessed."
        ),
    }), 200
