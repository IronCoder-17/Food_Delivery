# FoodExpress — Full-Stack Food Delivery Web Application

A complete food delivery platform with three separate ecosystems — **Customer**, **Restaurant**,
and **Admin** — built with React (frontend), Python/Flask (backend), and MySQL (database).

---

## 1. What's included

- **Customer**: OTP-verified registration, food browsing/search/filter, cart, checkout
  (Razorpay / COD / Wallet), order tracking, order history with printable receipts, wallet,
  General Knowledge game with server-verified scoring and random wallet rewards.
- **Restaurant**: application + admin-approval gating, profile management, food CRUD scoped to
  their own restaurant only, order management with a proper status state machine, dashboard stats.
- **Admin**: restaurant approval/rejection/deactivation, customer management, category management,
  food management across all restaurants, order + payment monitoring, GK question bank management.
- Role-based access control enforced **on the backend API**, not just hidden in the UI — a
  customer's token literally cannot call restaurant/admin endpoints, and vice versa.
- Passwords hashed with bcrypt, JWT session tokens, server-side validation on all sensitive
  operations (wallet debits, GK rewards, Razorpay signature verification).

---

## 2. Project structure

```
food-delivery-app/
├── backend/            Flask REST API (Python)
│   ├── app.py          App factory / entry point
│   ├── config/         Environment-driven configuration
│   ├── models/         SQLAlchemy models (mirrors database/schema.sql)
│   ├── routes/         Blueprints: auth, food, cart, orders, payments, wallet, game, restaurant, admin
│   ├── services/       OTP, wallet credit/debit business logic
│   ├── middleware/      JWT + role-based route protection
│   ├── utils/           Validators, auth helpers, seed_runner.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/            React app (Vite)
│   └── src/
│       ├── pages/customer, pages/restaurant, pages/admin, pages/auth
│       ├── components/  Shared UI (navbar, dashboard layout, food card, etc.)
│       ├── services/    API client (axios) + endpoint functions
│       └── hooks/       Auth + cart React context
├── database/
│   ├── schema.sql       Full normalized MySQL schema
│   └── seed.sql         States/cities/categories/GK questions (restaurants/foods/admin seeded via seed_runner.py so passwords are hashed correctly)
└── README.md            (this file)
```

---

## 3. Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- A MySQL 8.0+ server (local or hosted — e.g. RDS, PlanetScale, Azure MySQL, etc.)
- (Optional, for live payments) A Razorpay account and API keys

---

## 4. Backend setup

```bash
cd food-delivery-app/backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in:
#   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
#   SECRET_KEY, JWT_SECRET_KEY (any long random strings)
#   RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET (optional, for live payments)
```

### Create the database schema

Run the schema against your MySQL server:

```bash
mysql -h <host> -u <user> -p < ../database/schema.sql
mysql -h <host> -u <user> -p food_delivery < ../database/seed.sql
```

`schema.sql` creates the `food_delivery` database and all tables.
`seed.sql` seeds states/cities, categories, and the GK question bank.

### Seed admin + sample restaurants + sample food

This step also seeds states/categories/questions if you skipped the SQL files above
(it's idempotent — safe to run against a database that already has some of this data):

```bash
cd food-delivery-app          # repo root, not backend/
python -m backend.utils.seed_runner
```

This prints out the login credentials it creates, e.g.:

```
Created admin login -> email: admin@fooddelivery.com  password: Admin@123
Created restaurant -> email: spicevilla@example.com  password: Restaurant@123  (status: approved)
...
```

**Change these passwords** (or create your own admin/restaurant accounts) before going live.

### Run the backend

```bash
cd backend
python -m backend.app
```

The API will be available at `http://localhost:5000/api`. Check `http://localhost:5000/api/health`.

---

## 5. Frontend setup

```bash
cd food-delivery-app/frontend
npm install
echo "VITE_API_BASE=http://localhost:5000/api" > .env
npm run dev
```

Open `http://localhost:5173`.

For production build:

```bash
npm run build      # outputs to frontend/dist — serve with any static host / nginx
```

---

## 6. Logging in

- **Customer**: `http://localhost:5173/register` (OTP is simulated — see below)
- **Restaurant**: `http://localhost:5173/restaurant/login` (use a seeded account, or apply via
  `/restaurant/register` and approve it from the admin panel)
- **Admin**: `http://localhost:5173/admin/login` — this URL is intentionally not linked from the
  customer-facing navbar. Use the credentials printed by `seed_runner.py`.

### Seeded login credentials

These accounts are created automatically the first time you run
`python -m backend.utils.seed_runner` (see section 4). All restaurant accounts are seeded with
`status: approved`, so they can log in immediately without waiting on admin approval.

| Role       | Restaurant / Name    | Email                       | Password         |
|------------|----------------------|------------------------------|-------------------|
| Admin      | Platform Admin        | `admin@fooddelivery.com`     | `Admin@123`       |
| Restaurant | Spice Villa           | `spicevilla@example.com`     | `Restaurant@123`  |
| Restaurant | Urban Bites           | `urbanbites@example.com`     | `Restaurant@123`  |
| Restaurant | The Curry House       | `curryhouse@example.com`     | `Restaurant@123`  |
| Restaurant | Green Leaf Kitchen    | `greenleaf@example.com`      | `Restaurant@123`  |

> ⚠️ These are **development-only** credentials meant for local testing. Change them (or delete
> these accounts and create your own) before deploying anywhere publicly reachable.

---

## 7. Important notes on integrations that need your own credentials

### OTP (mobile verification)
No SMS gateway is configured. In `OTP_DEBUG_MODE=1` (the default), the generated OTP code is
returned directly in the API response (`dev_otp` field) and shown in the UI so you can test the
full registration flow without a real SMS provider. **Before going live**, wire a real provider
(Twilio, MSG91, etc.) into `backend/services/otp_service.py` and set `OTP_DEBUG_MODE=0`.

### Password reset emails
Same situation — no SMTP/email service is configured. The reset link is printed to the backend
console and returned as `dev_reset_token` in debug mode. Wire a real email provider into
`backend/routes/auth_routes.py` (`forgot_password`) before going live.

### Razorpay
The backend creates orders and verifies payment signatures server-side (`backend/routes/payment_routes.py`),
and the secret key is never sent to the frontend. Until you set `RAZORPAY_KEY_ID` /
`RAZORPAY_KEY_SECRET` in your `.env`, choosing "Razorpay" at checkout will return a clear
"not configured" error rather than faking a successful payment. Get test keys from your
[Razorpay Dashboard](https://dashboard.razorpay.com/) to test the full flow.

---

## 8. Security notes

- Passwords are hashed with bcrypt; nowhere in the API (including admin customer views) is a
  password or password hash ever returned.
- JWT tokens carry `role`, and every sensitive backend route is decorated with
  `@token_required([...])` restricting it to specific roles — enforced server-side, not just hidden
  in the UI.
- Wallet balance checks and debits happen entirely server-side (`backend/services/wallet_service.py`);
  the client can never manipulate its own balance.
- GK game rewards are generated server-side after the game session completes, guarded by a unique
  constraint on `game_rewards.session_id` so a session can only ever pay out once.
- Restaurant food management endpoints verify the food row belongs to the authenticated
  restaurant before allowing edits/deletes — cross-restaurant tampering returns 404.

---

## 9. Extending further

This is a complete, working v1 covering all core flows end-to-end. Natural next steps if you keep
building: saved multiple delivery addresses in the UI (the `addresses` table already supports it),
push/email notifications wired to a real provider, image uploads for food/restaurant photos
(currently URL-based), and a production WSGI server (gunicorn) + reverse proxy in front of Flask
for deployment.
