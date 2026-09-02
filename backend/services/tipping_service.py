"""
Dynamic Delivery Tipping.

Design note (why this isn't fake): the spec allows "distance" or "delivery
conditions" (e.g. weather) as example factors, but this codebase has no
restaurant/customer coordinate fields to compute a real distance, and no
weather API key is configured. Rather than fabricate a distance or weather
signal, tip suggestions here are computed transparently from the order's
own real subtotal -- a common, honest basis real delivery apps also use.
If a weather API key is later configured, this function is the one place
to extend with a real distance/weather factor.
"""

TIP_TIERS = [
    (0.10, "10% of your order"),
    (0.15, "15% of your order"),
    (0.20, "20% of your order"),
]


def suggest_tips(subtotal: float):
    subtotal = max(0.0, float(subtotal))
    return [
        {"amount": round(subtotal * pct, 2), "reason": reason}
        for pct, reason in TIP_TIERS
    ]
