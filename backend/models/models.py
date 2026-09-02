from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class State(db.Model):
    __tablename__ = "states"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class City(db.Model):
    __tablename__ = "cities"
    id = db.Column(db.Integer, primary_key=True)
    state_id = db.Column(db.Integer, db.ForeignKey("states.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # customer/restaurant/admin
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    mobile_verified = db.Column(db.Boolean, default=False)
    state_id = db.Column(db.Integer, db.ForeignKey("states.id"))
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    address = db.Column(db.Text)
    pincode = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    profile_image_url = db.Column(db.String(255), nullable=True)
    referral_code = db.Column(db.String(30), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---- Google Sign-In ----
    # google_id: the verified Google "sub" (subject) claim, unique per Google
    # account. Nullable because most customers still sign up with a password.
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    # auth_provider: "local" (email/password) or "google". Purely informational
    # (e.g. for showing "Signed in with Google" in the UI) -- a customer that
    # registered locally and later links Google still logs in with either.
    auth_provider = db.Column(db.String(20), nullable=False, default="local")
    # profile_completed: False only for brand-new Google sign-ups that still
    # need to supply mobile number / address / state / city (required fields
    # that Google does not provide). True for every normal registration.
    profile_completed = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", backref="customer_profile")


class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    label = db.Column(db.String(50), default="Home")
    contact_name = db.Column(db.String(150), nullable=True)
    contact_phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey("states.id"))
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    pincode = db.Column(db.String(10))
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    # Delivery Preferences: silent_drop / ring_bell / call_me. Saved per
    # address so it travels with wherever the customer is ordering to.
    delivery_instruction = db.Column(db.String(20), nullable=False, default="ring_bell")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Restaurant(db.Model):
    __tablename__ = "restaurants"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    restaurant_name = db.Column(db.String(150), nullable=False)
    owner_name = db.Column(db.String(120), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey("states.id"))
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    pincode = db.Column(db.String(10))
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(255))
    cover_image_url = db.Column(db.String(255))
    document_url = db.Column(db.String(255))
    opening_time = db.Column(db.String(8))
    closing_time = db.Column(db.String(8))
    status = db.Column(db.String(20), default="pending")  # pending/approved/rejected/deactivated
    rating = db.Column(db.Numeric(3, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="restaurant_profile")


class Admin(db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)


class OtpVerification(db.Model):
    __tablename__ = "otp_verifications"
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(15), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), default="registration")
    attempts = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Food(db.Model):
    __tablename__ = "foods"
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    is_veg = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percent = db.Column(db.Numeric(5, 2), default=0)
    image_url = db.Column(db.String(255))
    preparation_time_minutes = db.Column(db.Integer, default=20)
    is_available = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Numeric(3, 2), default=0)
    # ---- Inventory / sold-out management ----
    track_inventory = db.Column(db.Boolean, default=False, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=True)  # NULL = not tracked (unlimited)
    low_stock_threshold = db.Column(db.Integer, default=5, nullable=False)
    # ---- Nutrition Tracking (restaurant-provided estimates) ----
    calories = db.Column(db.Integer, nullable=True)
    protein_grams = db.Column(db.Numeric(6, 2), nullable=True)
    carbs_grams = db.Column(db.Numeric(6, 2), nullable=True)
    fat_grams = db.Column(db.Numeric(6, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = db.relationship("Restaurant", backref="foods")
    category = db.relationship("Category", backref="foods")

    @property
    def final_price(self):
        p = float(self.price)
        d = float(self.discount_percent or 0)
        return round(p - (p * d / 100), 2)

    @property
    def is_low_stock(self):
        if not self.track_inventory or self.stock_quantity is None:
            return False
        return self.stock_quantity <= self.low_stock_threshold


class Cart(db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), unique=True, nullable=False)


class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=True)
    combo_id = db.Column(db.Integer, db.ForeignKey("combos.id"), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    food = db.relationship("Food")
    combo = db.relationship("Combo")

    __table_args__ = (
        # Exactly one of food_id / combo_id must be set -- enforced in the
        # application layer (cart_routes.py) since a portable CHECK across
        # two nullable FKs isn't reliable across SQLite/MySQL versions.
    )


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    address_text = db.Column(db.Text, nullable=False)
    # Structured location snapshot -- populated only when checkout used a
    # saved Address (which has real city/pincode/coordinates). Left NULL for
    # freely-typed addresses: we genuinely don't know their structured
    # location, and we never guess/geocode it. Used only in aggregate by
    # the admin Order Heatmap -- never exposed as an individual pin.
    delivery_city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=True)
    delivery_pincode = db.Column(db.String(10), nullable=True)
    delivery_latitude = db.Column(db.Numeric(10, 7), nullable=True)
    delivery_longitude = db.Column(db.Numeric(10, 7), nullable=True)
    promotion_assignment_id = db.Column(db.Integer, db.ForeignKey("promotion_assignments.id"), nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # razorpay/cod/wallet
    payment_status = db.Column(db.String(20), default="pending")
    order_status = db.Column(db.String(30), default="placed")
    # Snapshot of the chosen Delivery Preference at checkout time (an
    # address's own default can change later -- the order keeps what was
    # true when it was placed). NULL for orders placed before this feature
    # existed, or with a freely-typed address that had no saved preference.
    delivery_instruction = db.Column(db.String(20), nullable=True)
    # ---- Dynamic Tipping, Eco Delivery, Micro-Donations ----
    tip_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    eco_delivery = db.Column(db.Boolean, nullable=False, default=False)
    donation_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", cascade="all,delete")
    restaurant = db.relationship("Restaurant")
    customer = db.relationship("Customer")
    delivery_city = db.relationship("City")


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=True)
    combo_id = db.Column(db.Integer, db.ForeignKey("combos.id"), nullable=True)
    food_name = db.Column(db.String(150), nullable=False)  # snapshot label -- food name or "Combo: X"
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)

    food = db.relationship("Food")
    combo = db.relationship("Combo")


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    method = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="pending")
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Wallet(db.Model):
    __tablename__ = "wallets"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0)
    total_credits = db.Column(db.Numeric(10, 2), default=0)
    total_debits = db.Column(db.Numeric(10, 2), default=0)


class WalletTransaction(db.Model):
    __tablename__ = "wallet_transactions"
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # credit/debit/bonus
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.String(150), nullable=False)
    reference_type = db.Column(db.String(20), nullable=False)  # order/game_reward/manual
    reference_id = db.Column(db.Integer)
    balance_after = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GameQuestion(db.Model):
    __tablename__ = "game_questions"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GameSession(db.Model):
    __tablename__ = "game_sessions"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    status = db.Column(db.String(20), default="in_progress")
    correct_count = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    reward_amount = db.Column(db.Numeric(10, 2), default=0)
    reward_claimed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)


class GameSessionQuestion(db.Model):
    __tablename__ = "game_session_questions"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("game_sessions.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("game_questions.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)


class GameAnswer(db.Model):
    __tablename__ = "game_answers"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("game_sessions.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("game_questions.id"), nullable=False)
    selected_option = db.Column(db.String(10), nullable=False)  # A/B/C/D/TIMEOUT
    is_correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)


class GameReward(db.Model):
    __tablename__ = "game_rewards"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("game_sessions.id"), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    wallet_transaction_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LoyaltyLevel(db.Model):
    __tablename__ = "loyalty_levels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    rank_order = db.Column(db.Integer, nullable=False, unique=True)  # 1=Bronze .. 6=Legends
    minimum_points = db.Column(db.Integer, nullable=False)
    maximum_points = db.Column(db.Integer, nullable=True)  # NULL = unbounded (top rank)
    benefits = db.Column(db.Text)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CustomerLoyalty(db.Model):
    __tablename__ = "customer_loyalty"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    lifetime_points = db.Column(db.Integer, default=0, nullable=False)
    rank = db.Column(db.String(30), default="Bronze", nullable=False)
    total_orders = db.Column(db.Integer, default=0, nullable=False)
    total_spending = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", backref=db.backref("loyalty", uselist=False))


class LoyaltyTransaction(db.Model):
    __tablename__ = "loyalty_transactions"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    points = db.Column(db.Integer, nullable=False)  # positive = earned, negative = deducted
    transaction_type = db.Column(db.String(20), nullable=False)  # earn/redeem/admin_add/admin_remove/reversal
    reference_type = db.Column(db.String(30))  # order/manual/refund
    reference_id = db.Column(db.Integer)
    description = db.Column(db.String(255))
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        # An order can only ever award loyalty points once (prevents duplicate rewards).
        db.UniqueConstraint("reference_type", "reference_id", "transaction_type",
                             name="uq_loyalty_txn_reference"),
    )


class AuthorityPermission(db.Model):
    __tablename__ = "authority_permissions"
    id = db.Column(db.Integer, primary_key=True)
    permission_key = db.Column(db.String(60), unique=True, nullable=False)  # e.g. customer.place_order
    permission_name = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # customer / restaurant
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    default_allowed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserAuthority(db.Model):
    __tablename__ = "user_authorities"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)  # Customer.id or Restaurant.id (not User.id)
    user_type = db.Column(db.String(20), nullable=False)  # customer / restaurant
    permission_id = db.Column(db.Integer, db.ForeignKey("authority_permissions.id"), nullable=False)
    is_allowed = db.Column(db.Boolean, default=True, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    permission = db.relationship("AuthorityPermission")

    __table_args__ = (
        db.UniqueConstraint("user_id", "user_type", "permission_id", name="uq_user_permission"),
    )


class AuthorityAuditLog(db.Model):
    __tablename__ = "authority_audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    permission = db.Column(db.String(60), nullable=False)
    previous_status = db.Column(db.Boolean, nullable=False)
    new_status = db.Column(db.Boolean, nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AiConversationLog(db.Model):
    """Lightweight log of AI assistant usage, useful for admin troubleshooting.
    Never stores another customer's data -- always scoped to one customer_id."""
    __tablename__ = "ai_conversation_logs"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    error = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FavoriteFood(db.Model):
    __tablename__ = "favorite_foods"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    food = db.relationship("Food")

    __table_args__ = (
        db.UniqueConstraint("customer_id", "food_id", name="uq_favorite_food"),
    )


class FavoriteRestaurant(db.Model):
    __tablename__ = "favorite_restaurants"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurant = db.relationship("Restaurant")

    __table_args__ = (
        db.UniqueConstraint("customer_id", "restaurant_id", name="uq_favorite_restaurant"),
    )


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="active")  # active / hidden (admin-moderated)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer")
    food = db.relationship("Food")
    restaurant = db.relationship("Restaurant")
    reply = db.relationship("ReviewReply", backref="review", uselist=False, cascade="all,delete")

    __table_args__ = (
        # One review per customer per food item per order -- prevents review farming
        # on the same delivered order, while still allowing a fresh review if the
        # customer orders the same dish again in a different order.
        db.UniqueConstraint("customer_id", "order_id", "food_id", name="uq_review_per_order_item"),
    )


class ReviewReply(db.Model):
    __tablename__ = "review_replies"
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), unique=True, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    reply_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Combo(db.Model):
    __tablename__ = "combos"
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    combo_price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = db.relationship("Restaurant")
    items = db.relationship("ComboItem", backref="combo", cascade="all,delete")

    @property
    def original_price(self):
        """Sum of each included food's current listed price * quantity --
        always computed live from Food, never stored/stale."""
        total = 0.0
        for item in self.items:
            if item.food:
                total += float(item.food.price) * item.quantity
        return round(total, 2)

    def is_currently_active(self):
        if not self.is_active:
            return False
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class ComboItem(db.Model):
    __tablename__ = "combo_items"
    id = db.Column(db.Integer, primary_key=True)
    combo_id = db.Column(db.Integer, db.ForeignKey("combos.id"), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    food = db.relationship("Food")


class FlashSale(db.Model):
    __tablename__ = "flash_sales"
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=True)
    combo_id = db.Column(db.Integer, db.ForeignKey("combos.id"), nullable=True)
    discount_percent = db.Column(db.Numeric(5, 2), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    max_quantity = db.Column(db.Integer, nullable=True)  # NULL = unlimited
    sold_quantity = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    food = db.relationship("Food")
    combo = db.relationship("Combo")

    def is_currently_live(self):
        if not self.is_active:
            return False
        now = datetime.utcnow()
        if now < self.start_time or now > self.end_time:
            return False
        if self.max_quantity is not None and self.sold_quantity >= self.max_quantity:
            return False
        return True


class ScheduledOrder(db.Model):
    __tablename__ = "scheduled_orders"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    address_text = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cod or wallet only (see service docstring)
    scheduled_for = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default="scheduled")  # scheduled/completed/cancelled/failed
    failure_reason = db.Column(db.String(255), nullable=True)
    created_order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer")
    restaurant = db.relationship("Restaurant")
    created_order = db.relationship("Order")
    items = db.relationship("ScheduledOrderItem", backref="scheduled_order", cascade="all,delete")


class ScheduledOrderItem(db.Model):
    __tablename__ = "scheduled_order_items"
    id = db.Column(db.Integer, primary_key=True)
    scheduled_order_id = db.Column(db.Integer, db.ForeignKey("scheduled_orders.id"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    food = db.relationship("Food")


class MealPlan(db.Model):
    __tablename__ = "meal_plans"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=True)
    days = db.Column(db.Integer, nullable=False)
    meals_per_day = db.Column(db.Integer, nullable=False)
    budget = db.Column(db.Numeric(10, 2), nullable=True)
    is_veg = db.Column(db.Boolean, nullable=True)  # None = no preference
    max_spend_per_meal = db.Column(db.Numeric(10, 2), nullable=True)
    estimated_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    summary_note = db.Column(db.Text, nullable=True)  # short AI-written or template intro
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer")
    restaurant = db.relationship("Restaurant")
    items = db.relationship("MealPlanItem", backref="meal_plan", cascade="all,delete", order_by="MealPlanItem.day_index,MealPlanItem.meal_index")


class MealPlanItem(db.Model):
    __tablename__ = "meal_plan_items"
    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plans.id"), nullable=False, index=True)
    day_index = db.Column(db.Integer, nullable=False)  # 0-based
    meal_index = db.Column(db.Integer, nullable=False)  # 0-based within the day
    meal_label = db.Column(db.String(30), nullable=False)  # e.g. "Dinner", "Meal 2"
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    price_at_planning = db.Column(db.Numeric(10, 2), nullable=True)  # snapshot for display only, re-validated at Build Cart
    unavailable_reason = db.Column(db.String(150), nullable=True)  # set if no food could fill this slot

    food = db.relationship("Food")


class GroupOrder(db.Model):
    __tablename__ = "group_orders"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    host_customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    invite_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="open")  # open / locked / completed / cancelled
    created_order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    # ---- Voting + config (all optional; the direct-add shared cart keeps
    # working exactly as before if these are left unset) ----
    enable_voting = db.Column(db.Boolean, nullable=False, default=False)
    voting_deadline = db.Column(db.DateTime, nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)
    budget = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    host = db.relationship("Customer")
    restaurant = db.relationship("Restaurant")
    created_order = db.relationship("Order")
    members = db.relationship("GroupOrderMember", backref="group_order", cascade="all,delete")
    items = db.relationship("GroupOrderItem", backref="group_order", cascade="all,delete")

    def is_past_deadline(self):
        return bool(self.deadline and datetime.utcnow() > self.deadline)


class GroupOrderMember(db.Model):
    __tablename__ = "group_order_members"
    id = db.Column(db.Integer, primary_key=True)
    group_order_id = db.Column(db.Integer, db.ForeignKey("group_orders.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer")

    __table_args__ = (db.UniqueConstraint("group_order_id", "customer_id", name="uq_group_member"),)


class GroupOrderItem(db.Model):
    __tablename__ = "group_order_items"
    id = db.Column(db.Integer, primary_key=True)
    group_order_id = db.Column(db.Integer, db.ForeignKey("group_orders.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)  # who added it
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer")
    food = db.relationship("Food")


class ReferralConfig(db.Model):
    __tablename__ = "referral_configs"
    id = db.Column(db.Integer, primary_key=True)
    referrer_points = db.Column(db.Integer, default=100, nullable=False)
    referred_points = db.Column(db.Integer, default=50, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Referral(db.Model):
    __tablename__ = "referrals"
    id = db.Column(db.Integer, primary_key=True)
    referrer_customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    referred_customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), unique=True, nullable=False)
    referral_code_used = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / completed / blocked
    qualifying_order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    referrer = db.relationship("Customer", foreign_keys=[referrer_customer_id])
    referred = db.relationship("Customer", foreign_keys=[referred_customer_id])
    qualifying_order = db.relationship("Order")


class OrderTrackingEvent(db.Model):
    __tablename__ = "order_tracking_events"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SubscriptionPlan(db.Model):
    __tablename__ = "subscription_plans"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g. Basic / Pro / Premium
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    granted_permissions = db.Column(db.Text, nullable=True)  # comma-separated restaurant.* permission keys
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def permission_list(self):
        return [p.strip() for p in (self.granted_permissions or "").split(",") if p.strip()]


class RestaurantSubscription(db.Model):
    __tablename__ = "restaurant_subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / active / expired / cancelled
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    activated_by_admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)

    restaurant = db.relationship("Restaurant")
    plan = db.relationship("SubscriptionPlan")

    def is_currently_active(self):
        return self.status == "active" and self.expires_at > datetime.utcnow()


class SponsoredCampaign(db.Model):
    __tablename__ = "sponsored_campaigns"
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    placement = db.Column(db.String(50), default="homepage")  # e.g. homepage, search_top
    priority = db.Column(db.Integer, default=0)  # higher = shown first among sponsored slots
    budget = db.Column(db.Numeric(10, 2), nullable=True)
    campaign_start = db.Column(db.DateTime, nullable=False)
    campaign_end = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurant = db.relationship("Restaurant")

    def is_currently_live(self):
        now = datetime.utcnow()
        return self.is_active and self.campaign_start <= now <= self.campaign_end


class PassPlan(db.Model):
    __tablename__ = "pass_plans"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g. "QuickBite Pass"
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    min_order_amount = db.Column(db.Numeric(10, 2), default=0)
    max_free_deliveries_per_period = db.Column(db.Integer, default=4, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    eligible_restaurants = db.relationship("PassPlanRestaurant", backref="plan", cascade="all,delete")


class PassPlanRestaurant(db.Model):
    """If a plan has ANY rows here, it's restricted to those restaurants.
    If it has none, it's valid at every restaurant."""
    __tablename__ = "pass_plan_restaurants"
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("pass_plans.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)

    restaurant = db.relationship("Restaurant")


class QuickBitePass(db.Model):
    __tablename__ = "quickbite_passes"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("pass_plans.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="active")  # active / expired / cancelled
    current_period_index = db.Column(db.Integer, default=0, nullable=False)
    deliveries_used_in_period = db.Column(db.Integer, default=0, nullable=False)

    customer = db.relationship("Customer")
    plan = db.relationship("PassPlan")

    def is_currently_active(self):
        return self.status == "active" and self.expires_at > datetime.utcnow()


class DeliveryBenefitUsage(db.Model):
    __tablename__ = "delivery_benefit_usage"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    pass_id = db.Column(db.Integer, db.ForeignKey("quickbite_passes.id"), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FraudFlag(db.Model):
    __tablename__ = "fraud_flags"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    rule = db.Column(db.String(60), nullable=False)  # e.g. "repeated_cod_cancellations"
    reason = db.Column(db.String(255), nullable=False)
    incident_count = db.Column(db.Integer, default=1, nullable=False)
    risk_score = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    status = db.Column(db.String(20), default="review")  # review / warning / restricted / cleared
    reviewed_by_admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer")


class PromotionExperiment(db.Model):
    __tablename__ = "promotion_experiments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    variant_a_label = db.Column(db.String(100), default="Promotion A")
    variant_b_label = db.Column(db.String(100), default="Promotion B")
    discount_percent_a = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    discount_percent_b = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    status = db.Column(db.String(20), default="draft")  # draft / running / completed
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignments = db.relationship("PromotionAssignment", backref="experiment", cascade="all,delete")

    def is_currently_running(self):
        if self.status != "running":
            return False
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class PromotionAssignment(db.Model):
    __tablename__ = "promotion_assignments"
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey("promotion_experiments.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    variant = db.Column(db.String(1), nullable=False)  # 'A' or 'B'
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("experiment_id", "customer_id", name="uq_promo_assignment"),)


class DisputeTicket(db.Model):
    __tablename__ = "dispute_tickets"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    reason = db.Column(db.String(30), nullable=False)  # missing_item/wrong_item/damaged_item/payment_issue/delivery_issue/other
    description = db.Column(db.Text, nullable=True)
    evidence_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default="open")  # open/under_review/waiting_for_restaurant/resolved/rejected
    resolution_note = db.Column(db.Text, nullable=True)
    refund_amount = db.Column(db.Numeric(10, 2), nullable=True)
    resolved_by_admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = db.relationship("Order")
    customer = db.relationship("Customer")
    restaurant = db.relationship("Restaurant")
    events = db.relationship("DisputeEvent", backref="dispute", cascade="all,delete", order_by="DisputeEvent.created_at")


class DisputeEvent(db.Model):
    __tablename__ = "dispute_events"
    id = db.Column(db.Integer, primary_key=True)
    dispute_id = db.Column(db.Integer, db.ForeignKey("dispute_tickets.id"), nullable=False, index=True)
    actor_type = db.Column(db.String(20), nullable=False)  # customer / admin
    actor_id = db.Column(db.Integer, nullable=True)
    event_type = db.Column(db.String(30), nullable=False)  # created/status_change/resolution/note
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    recipient_role = db.Column(db.String(20), nullable=False)
    recipient_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =============================================================================
# Batch 1 Feature Upgrade: Mood-Based Ordering, Ingredient & Allergen Tags,
# Live Kitchen Load, Chef's Specials, Food Streaks.
# (Delivery Preferences added columns directly to Address/Order above.
#  Order Again / Reorder already existed -- see reorder_routes.py.)
# =============================================================================

class FoodMood(db.Model):
    """A mood/craving tag customers can filter by (Comfort Food, Quick Bite,
    etc). Seeded with a fixed starter set by the migration; admin can
    activate/deactivate but the list isn't meant to be freely user-created,
    to keep the discovery UI consistent."""
    __tablename__ = "food_moods"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    emoji = db.Column(db.String(10), nullable=False, default="🍽️")
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class FoodMoodMapping(db.Model):
    __tablename__ = "food_mood_mapping"
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True)
    mood_id = db.Column(db.Integer, db.ForeignKey("food_moods.id", ondelete="CASCADE"), primary_key=True)

    mood = db.relationship("FoodMood")


class FoodAllergen(db.Model):
    """Ingredient/allergen tag (Vegan, Contains Nuts, Gluten-free, ...).
    Restaurant-provided information -- see the disclaimer surfaced
    everywhere this is displayed to customers."""
    __tablename__ = "food_allergens"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class FoodAllergenMapping(db.Model):
    __tablename__ = "food_allergen_mapping"
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True)
    allergen_id = db.Column(db.Integer, db.ForeignKey("food_allergens.id", ondelete="CASCADE"), primary_key=True)

    allergen = db.relationship("FoodAllergen")


class RestaurantKitchenStatus(db.Model):
    """Live kitchen load, restaurant-set. One row per restaurant (created
    lazily on first status update; treated as 'normal, +0 min' if absent)."""
    __tablename__ = "restaurant_kitchen_status"
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id", ondelete="CASCADE"), primary_key=True)
    status = db.Column(db.String(20), nullable=False, default="normal")  # normal/busy/very_busy/overloaded
    extra_minutes = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChefSpecial(db.Model):
    """Restaurant's limited-time, limited-quantity Chef's Special at an
    explicit special_price (distinct from the percent-off FlashSale system).
    First-come-first-served: quantity_sold is only ever incremented
    server-side at the moment an order is actually placed."""
    __tablename__ = "chef_specials"
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)
    special_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_total = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False, default=0)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    food = db.relationship("Food")
    restaurant = db.relationship("Restaurant")

    def is_currently_live(self):
        if not self.is_active:
            return False
        now = datetime.utcnow()
        if now < self.start_time or now > self.end_time:
            return False
        if self.quantity_sold >= self.quantity_total:
            return False
        return True

    @property
    def remaining_quantity(self):
        return max(0, self.quantity_total - self.quantity_sold)


class FoodStreak(db.Model):
    """Engagement streak (NOT a purchase requirement -- logging in, playing
    the GK game, or placing an order all count as one day's activity).
    Milestone rewards are guarded by last_milestone_awarded so the same
    milestone can never pay out twice."""
    __tablename__ = "food_streaks"
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    current_streak = db.Column(db.Integer, nullable=False, default=0)
    best_streak = db.Column(db.Integer, nullable=False, default=0)
    streak_points = db.Column(db.Integer, nullable=False, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)
    last_milestone_awarded = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Batch 2/3 Feature Upgrade: Group Order Voting + Bill Splitting, Surplus
# Deals, Packing Photo Proof, Micro-Donations, Nutrition Tracking.
# (Dynamic Tipping and Eco Delivery added columns directly to Order above.
#  Recipe-to-Order is implemented as a stateless matching endpoint --
#  see backend/services/recipe_service.py -- so it has no table here.)
# =============================================================================

class GroupOrderSuggestion(db.Model):
    """A dish suggested for group voting. Distinct from GroupOrderItem
    (the direct-add shared cart) -- a suggestion only becomes a real cart
    item if it wins the vote (see group_voting_service.finalize_voting)."""
    __tablename__ = "group_order_suggestions"
    id = db.Column(db.Integer, primary_key=True)
    group_order_id = db.Column(db.Integer, db.ForeignKey("group_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    suggested_by_customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    food = db.relationship("Food")
    suggested_by = db.relationship("Customer")
    votes = db.relationship("GroupOrderVote", backref="suggestion", cascade="all,delete")

    __table_args__ = (db.UniqueConstraint("group_order_id", "food_id", name="uq_group_suggestion"),)


class GroupOrderVote(db.Model):
    __tablename__ = "group_order_votes"
    id = db.Column(db.Integer, primary_key=True)
    suggestion_id = db.Column(db.Integer, db.ForeignKey("group_order_suggestions.id", ondelete="CASCADE"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("suggestion_id", "customer_id", name="uq_one_vote_per_member"),)


class GroupOrderPayment(db.Model):
    """Bill-split reimbursement. The group order's real Order is already
    fully paid by the host at checkout (unchanged, existing flow) -- this
    is each OTHER member's real-money share, paid via their own Wallet,
    credited to the host's Wallet. See group_bill_service.py for why this
    (not a simulated UPI flow) is the honest design given no external
    payment-collection integration exists in this codebase."""
    __tablename__ = "group_order_payments"
    id = db.Column(db.Integer, primary_key=True)
    group_order_id = db.Column(db.Integer, db.ForeignKey("group_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    split_type = db.Column(db.String(20), nullable=False)  # equal / item_based
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/paid/failed/refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    customer = db.relationship("Customer")

    __table_args__ = (db.UniqueConstraint("group_order_id", "customer_id", name="uq_one_share_per_member"),)


class SurplusDeal(db.Model):
    """Restaurant-listed near-expiry/surplus food at a discount. The
    restaurant remains responsible for food safety -- this system only
    tracks price/quantity/timing, never makes a safety claim."""
    __tablename__ = "surplus_deals"
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False, index=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)
    original_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_total = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False, default=0)
    order_deadline = db.Column(db.DateTime, nullable=False)
    expiry_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    food = db.relationship("Food")
    restaurant = db.relationship("Restaurant")

    def is_currently_available(self):
        if not self.is_active:
            return False
        now = datetime.utcnow()
        if now > self.order_deadline or now > self.expiry_time:
            return False
        if self.quantity_sold >= self.quantity_total:
            return False
        return True

    @property
    def remaining_quantity(self):
        return max(0, self.quantity_total - self.quantity_sold)

    @property
    def discount_percent(self):
        if not self.original_price:
            return 0
        return round((1 - float(self.discount_price) / float(self.original_price)) * 100, 1)


class OrderPackingProof(db.Model):
    """Restaurant-uploaded packing photo. image_path is a server filesystem
    path, NEVER a public URL -- access is gated by order ownership (the
    customer who placed it, the restaurant that packed it, or an admin),
    enforced in packing_proof_routes.py, never served as a static file."""
    __tablename__ = "order_packing_proofs"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    image_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class NutritionLog(db.Model):
    """One entry per order a customer chooses to log. Values are a snapshot
    at logging time (restaurant-provided estimates, not medical advice)."""
    __tablename__ = "nutrition_logs"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    calories = db.Column(db.Integer, nullable=False, default=0)
    protein_grams = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    carbs_grams = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    fat_grams = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    logged_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("customer_id", "order_id", name="uq_one_log_per_order"),)
