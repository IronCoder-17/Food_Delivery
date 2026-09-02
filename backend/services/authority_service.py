"""
Centralized Authority Management engine.

Every permission check in the whole application (frontend visibility AND
backend enforcement) is driven from the `authority_permissions` /
`user_authorities` tables via this module, so there is exactly one source
of truth for "is this customer/restaurant allowed to do X".
"""
from functools import wraps
from flask import g, jsonify

from backend.models.models import db, AuthorityPermission, UserAuthority, AuthorityAuditLog, Customer, Restaurant

# ---------------------------------------------------------------------------
# Permission catalog. Adding a new key here + running ensure_default_permissions()
# is all that's needed to introduce a new governable permission.
# ---------------------------------------------------------------------------
CUSTOMER_PERMISSIONS = [
    ("customer.login", "Login", "Can log in to the platform."),
    ("customer.view_food", "View Food", "Can browse food items."),
    ("customer.search_food", "Search Food", "Can search for food items."),
    ("customer.filter_food", "Filter Food", "Can filter food listings."),
    ("customer.view_restaurant", "View Restaurant", "Can view restaurant listings/details."),
    ("customer.add_cart", "Add to Cart", "Can add items to the cart."),
    ("customer.place_order", "Place Order", "Can place an order at checkout."),
    ("customer.cod", "Cash on Delivery", "Can pay via Cash on Delivery."),
    ("customer.online_payment", "Online Payment", "Can pay via Razorpay online payment."),
    ("customer.wallet", "Wallet", "Can use wallet balance/features."),
    ("customer.view_orders", "View Orders", "Can view own order history."),
    ("customer.cancel_order", "Cancel Order", "Can cancel an eligible order."),
    ("customer.track_order", "Track Order", "Can track order status."),
    ("customer.ai_assistant", "AI Assistant", "Can use the AI Assistant chat."),
    ("customer.loyalty", "Loyalty System", "Can access the loyalty/rank dashboard."),
    ("customer.use_loyalty_points", "Use Loyalty Points", "Can redeem loyalty points."),
    ("customer.view_profile", "View Profile", "Can view own profile."),
    ("customer.edit_profile", "Edit Profile", "Can edit own profile."),
    ("customer.send_messages", "Send Messages", "Can send messages/support queries."),
    ("customer.receive_notifications", "Receive Notifications", "Can receive notifications."),
    ("customer.manage_addresses", "Manage Saved Addresses", "Can add/edit/delete saved delivery addresses."),
    ("customer.favorites", "Favorites / Wishlist", "Can favorite foods and restaurants."),
    ("customer.reviews", "Reviews & Ratings", "Can write reviews for delivered orders."),
    ("customer.reorder", "One-Tap Reorder", "Can re-add items from a past order to the cart."),
    ("customer.scheduled_orders", "Scheduled Orders", "Can schedule an order for a future date/time."),
    ("customer.meal_planner", "AI Meal Planner", "Can generate an AI-assisted weekly meal plan."),
    ("customer.voice_ordering", "Voice Ordering", "Can use microphone voice input with the AI Assistant."),
    ("customer.group_ordering", "Group Ordering", "Can create/join shared group orders."),
    ("customer.referrals", "Referrals", "Can view/share their referral code and rewards."),
    ("customer.quickbite_pass", "QuickBite Pass", "Can subscribe to and use the delivery-fee subscription."),
    ("customer.disputes", "Disputes", "Can open a dispute for an eligible order."),
    ("customer.mood_filter", "Mood-Based Ordering", "Can browse/filter foods by mood tag."),
    ("customer.allergen_filter", "Allergen Filtering", "Can filter foods by ingredient/allergen tag."),
    ("customer.food_streaks", "Food Streaks", "Can view and earn rewards from the engagement streak."),
    ("customer.chefs_specials", "Chef's Specials", "Can view and order Chef's Specials."),
    ("customer.surplus_deals", "Surplus Deals", "Can view and order Surplus/Leftover Deals."),
    ("customer.group_voting", "Group Order Voting", "Can suggest and vote on dishes in a group order."),
    ("customer.group_bill_split", "Group Bill Splitting", "Can request and pay a bill-split share for a group order."),
    ("customer.donations", "Micro-Donations", "Can round up an order total as a donation."),
    ("customer.nutrition_tracking", "Nutrition Tracking", "Can log and view nutrition summaries."),
    ("customer.recipe_to_order", "Recipe-to-Order", "Can match a recipe/ingredients against the menu."),
    ("customer.photo_reorder", "Photo Reorder", "Can upload a dish photo to find matching menu items."),
    ("customer.eco_delivery", "Eco Delivery", "Can opt into eco-friendly delivery at checkout."),
]

RESTAURANT_PERMISSIONS = [
    ("restaurant.login", "Login", "Can log in to the platform."),
    ("restaurant.dashboard", "Restaurant Dashboard", "Can access the restaurant dashboard."),
    ("restaurant.view_profile", "View Profile", "Can view own restaurant profile."),
    ("restaurant.edit_profile", "Edit Restaurant Profile", "Can edit own restaurant profile."),
    ("restaurant.manage_food", "Manage Food", "Master switch for all food management actions."),
    ("restaurant.add_food", "Add Food", "Can add new food items."),
    ("restaurant.edit_food", "Edit Food", "Can edit existing food items."),
    ("restaurant.delete_food", "Delete Food", "Can delete food items."),
    ("restaurant.set_price", "Set Food Price", "Can set/change food prices."),
    ("restaurant.set_veg_nonveg", "Set Veg/Non-Veg", "Can set the veg/non-veg flag."),
    ("restaurant.manage_categories", "Manage Categories", "Can assign food categories."),
    ("restaurant.view_orders", "View Orders", "Can view incoming orders."),
    ("restaurant.accept_order", "Accept Orders", "Can accept a placed order."),
    ("restaurant.reject_order", "Reject Orders", "Can reject/cancel a placed order."),
    ("restaurant.update_order", "Update Order Status", "Can progress order status."),
    ("restaurant.view_customers", "View Customers", "Can view customer info tied to own orders."),
    ("restaurant.analytics", "Restaurant Analytics", "Can view own analytics/reports."),
    ("restaurant.receive_notifications", "Receive Notifications", "Can receive notifications."),
    ("restaurant.manage_availability", "Manage Availability", "Can toggle food/restaurant availability."),
    ("restaurant.reply_reviews", "Reply to Reviews", "Can post a reply to a customer review."),
    ("restaurant.manage_combos", "Manage Combos", "Can create/edit/delete combo meals."),
    ("restaurant.manage_flash_sales", "Manage Flash Sales", "Can create/edit/delete time-boxed flash sales."),
    ("restaurant.manage_inventory", "Manage Inventory", "Can set stock levels and sold-out thresholds."),
    ("restaurant.advanced_analytics", "Advanced Analytics", "Can view advanced peak-hour and revenue analytics (subscription-gated)."),
    ("restaurant.promotional_tools", "Promotional Tools", "Can access advanced promotional tools (subscription-gated)."),
    ("restaurant.sponsored_eligible", "Sponsored Placement Eligible", "Eligible for featured/sponsored placement (subscription-gated)."),
    ("restaurant.manage_kitchen_status", "Manage Kitchen Status", "Can update live kitchen load status."),
    ("restaurant.manage_chefs_specials", "Manage Chef's Specials", "Can create/edit/delete Chef's Specials."),
    ("restaurant.manage_food_tags", "Manage Food Tags", "Can assign mood and allergen tags to food items."),
    ("restaurant.manage_surplus_deals", "Manage Surplus Deals", "Can create/edit/delete Surplus/Leftover Deals."),
    ("restaurant.upload_packing_proof", "Upload Packing Proof", "Can upload a packing photo for an order."),
    ("restaurant.manage_nutrition_info", "Manage Nutrition Info", "Can set nutrition estimates on food items."),
]

ALL_PERMISSIONS = [(k, n, d, "customer") for k, n, d in CUSTOMER_PERMISSIONS] + \
                  [(k, n, d, "restaurant") for k, n, d in RESTAURANT_PERMISSIONS]


def ensure_default_permissions():
    """Idempotently create catalog rows for every permission key above.
    Safe to call on every app startup."""
    existing = {p.permission_key for p in AuthorityPermission.query.all()}
    created = False
    for key, name, desc, user_type in ALL_PERMISSIONS:
        if key in existing:
            continue
        db.session.add(AuthorityPermission(
            permission_key=key, permission_name=name, user_type=user_type,
            description=desc, is_active=True, default_allowed=True,
        ))
        created = True
    if created:
        db.session.commit()

    # Subscription-gated restaurant permissions must default to DENIED --
    # a restaurant only gets them via an active paid subscription
    # (see subscription_service.activate()), never automatically.
    SUBSCRIPTION_GATED_DEFAULT_DENY = {
        "restaurant.advanced_analytics", "restaurant.promotional_tools", "restaurant.sponsored_eligible",
    }
    changed = False
    for perm in AuthorityPermission.query.filter(
        AuthorityPermission.permission_key.in_(SUBSCRIPTION_GATED_DEFAULT_DENY)
    ).all():
        if perm.default_allowed:
            perm.default_allowed = False
            changed = True
    if changed:
        db.session.commit()


def assign_default_authorities(user_id: int, user_type: str):
    """Called right after a new customer/restaurant registers: gives them
    a UserAuthority row for every currently configured permission of their
    type, using each permission's configured default_allowed value."""
    perms = AuthorityPermission.query.filter_by(user_type=user_type, is_active=True).all()
    for perm in perms:
        if UserAuthority.query.filter_by(user_id=user_id, user_type=user_type, permission_id=perm.id).first():
            continue
        db.session.add(UserAuthority(
            user_id=user_id, user_type=user_type, permission_id=perm.id,
            is_allowed=perm.default_allowed,
        ))
    db.session.commit()


def get_effective_authorities(user_id: int, user_type: str) -> dict:
    """Returns {permission_key: bool} for every permission of this user_type.
    Missing rows (e.g. permission added after the user registered) default
    to that permission's configured default_allowed value, so nothing is
    silently un-governed."""
    perms = AuthorityPermission.query.filter_by(user_type=user_type, is_active=True).all()
    existing = {
        ua.permission_id: ua.is_allowed
        for ua in UserAuthority.query.filter_by(user_id=user_id, user_type=user_type).all()
    }
    return {p.permission_key: existing.get(p.id, p.default_allowed) for p in perms}


def has_permission(user_id: int, user_type: str, permission_key: str) -> bool:
    perm = AuthorityPermission.query.filter_by(permission_key=permission_key, user_type=user_type).first()
    if not perm or not perm.is_active:
        # Unknown/deactivated permission keys never silently grant access.
        return False
    ua = UserAuthority.query.filter_by(user_id=user_id, user_type=user_type, permission_id=perm.id).first()
    if ua is not None:
        return bool(ua.is_allowed)
    return bool(perm.default_allowed)


def set_authority(user_id: int, user_type: str, permission_key: str, is_allowed: bool,
                   admin_id: int, reason: str = None):
    """Sets one permission for one user, records an audit log entry, and
    returns (previous_status, new_status). Raises ValueError if the
    permission key doesn't exist for that user_type."""
    perm = AuthorityPermission.query.filter_by(permission_key=permission_key, user_type=user_type).first()
    if not perm:
        raise ValueError(f"Unknown permission '{permission_key}' for user_type '{user_type}'.")

    ua = UserAuthority.query.filter_by(user_id=user_id, user_type=user_type, permission_id=perm.id).first()
    previous = ua.is_allowed if ua else perm.default_allowed

    if not ua:
        ua = UserAuthority(user_id=user_id, user_type=user_type, permission_id=perm.id)
        db.session.add(ua)

    ua.is_allowed = bool(is_allowed)
    ua.updated_by = admin_id

    db.session.add(AuthorityAuditLog(
        admin_id=admin_id, user_id=user_id, user_type=user_type, permission=permission_key,
        previous_status=bool(previous), new_status=bool(is_allowed), reason=reason,
    ))
    db.session.commit()
    return previous, bool(is_allowed)


def require_permission(permission_key: str):
    """
    Backend-enforced permission gate. Use *after* @token_required so g.role
    and g.user_id are already populated. Resolves the caller's
    Customer.id/Restaurant.id from their authenticated user id (never from
    client input), then checks user_authorities. Returns 403 Forbidden if
    the admin has disabled this permission for this specific user.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = g.role
            if role not in ("customer", "restaurant"):
                # Admins bypass authority gates (they configure the gates themselves).
                return fn(*args, **kwargs)

            if role == "customer":
                profile = Customer.query.filter_by(user_id=g.user_id).first()
            else:
                profile = Restaurant.query.filter_by(user_id=g.user_id).first()

            if not profile:
                return jsonify({"error": "Profile not found."}), 404

            if not has_permission(profile.id, role, permission_key):
                return jsonify({
                    "error": "Forbidden: this action has been restricted by the administrator.",
                    "permission": permission_key,
                }), 403

            g.authority_profile_id = profile.id
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def serialize_permission(p: AuthorityPermission):
    return {
        "id": p.id, "permission_key": p.permission_key, "permission_name": p.permission_name,
        "user_type": p.user_type, "description": p.description, "is_active": p.is_active,
        "default_allowed": p.default_allowed,
    }
