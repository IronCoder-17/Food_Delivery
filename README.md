# QuickBite — Full-Stack Food Delivery Web Application

A full-stack food delivery platform with three separate portals — **Customer**, **Restaurant**,
and **Admin** — built with **React (Vite)** on the frontend, **Python/Flask** on the backend, and
**MySQL** for storage. It goes well beyond a basic ordering flow: loyalty & referrals, group
ordering, meal planning, subscriptions, flash sales, surplus deals, fraud detection, disputes,
and more are all included.

---

## 1. What's included

**Customer**
- OTP-verified registration/login, Google Sign-In, password reset
- Food browsing/search/filter, cart, checkout (Razorpay / COD / Wallet), delivery addresses,
  favorites, ratings & reviews
- Order history, live order tracking, scheduled orders, reordering, photo-based reorder, AI
  recipe-to-order and AI assistant chat
- Loyalty points, referral program, wallet, food streaks, meal planner, group ordering with
  voting & bill splitting, "Quick Bite" pass/subscriptions, chef specials, surplus/flash deals,
  nutrition info, disputes, and a General Knowledge mini-game with server-verified wallet rewards

**Restaurant**
- Application + admin-approval gating, profile management
- Food CRUD scoped to their own restaurant, combos, flash sales, chef specials, surplus deals
- Order management with a proper status state machine, kitchen status tracking, subscription/plan
  management

**Admin**
- Restaurant approval/rejection/deactivation, customer management, category & food management
  across all restaurants
- Orders & payments monitoring, promotions, loyalty, referrals, passes/subscriptions, sponsored
  listings, disputes, fraud detection center, GK question bank, analytics dashboards (order
  heatmap, peak-hour analytics)

**Platform-wide**
- Role-based access control enforced **on the backend API**, not just hidden in the UI — a
  customer's token cannot call restaurant/admin endpoints, and vice versa
- Passwords hashed with bcrypt, JWT session tokens, server-side validation on all sensitive
  operations (wallet debits, GK rewards, Razorpay signature verification, fraud checks)

---

## 2. Project structure

```
food-delivery-app/
├── backend/                Flask REST API (Python)
│   ├── app.py              App factory / entry point (registers ~35 blueprints)
│   ├── config/             Environment-driven configuration
│   ├── models/             SQLAlchemy models (mirrors database/schema.sql + migrations)
│   ├── routes/             ~40 blueprint modules: auth, food, cart, orders, payments, wallet,
│   │                       game, restaurant, admin, loyalty, referrals, group orders, meal
│   │                       planner, passes, subscriptions, sponsored listings, fraud, disputes,
│   │                       promotions, kitchen, chef specials, streaks, surplus deals, recipes,
│   │                       photo reorder, nutrition, analytics, and more
│   ├── services/           Business logic layer (one service per domain — pricing, wallet,
│   │                       fraud, loyalty, promotions, subscriptions, AI, nutrition, etc.)
│   ├── middleware/         JWT + role-based route protection
│   ├── utils/              Validators, auth helpers, seed_runner.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                React app (Vite)
│   └── src/
│       ├── pages/customer/     ~20 customer pages (dashboard, cart, checkout, orders, wallet,
│       │                       loyalty, referrals, meal planner, group orders, AI assistant, ...)
│       ├── pages/restaurant/   Restaurant dashboard, foods, orders, combos, flash sales,
│       │                       chef specials, surplus deals, subscription, kitchen status
│       ├── pages/admin/        Admin dashboard, restaurants, customers, categories, foods,
│       │                       orders/payments, promotions, loyalty, fraud center, disputes,
│       │                       analytics (heatmap, peak-hour), passes
│       ├── pages/auth/         Customer/restaurant/admin login & registration, password reset
│       ├── components/         Shared UI (navbars, layouts, cards, theme toggle, etc.)
│       ├── services/           Axios API client + endpoint definitions
│       └── hooks/               Auth, Cart, Theme, Authority React contexts
├── database/
│   ├── schema.sql           Full normalized MySQL schema (base tables)
│   ├── migrations/          13 incremental migrations layering on later features:
│   │                        addresses/favorites/reviews, combos/flash sales/inventory,
│   │                        meal planner, group ordering, referrals, order tracking,
│   │                        passes/subscriptions/sponsored listings, order location,
│   │                        fraud/promotions/disputes, Google OAuth, two feature batches,
│   │                        and hashed password-reset tokens for real email delivery
│   └── seed.sql              States/cities/categories/GK questions (restaurants/foods/admin are
│                              seeded via seed_runner.py so passwords are hashed correctly)
└── README.md                 (this file)
```

---

## 3. Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- A MySQL 8.0+ server (local or hosted — e.g. RDS, PlanetScale, Azure MySQL, etc.)
- (Optional, for live payments) A Razorpay account and API keys
- (Optional, for the AI assistant / recipe-to-order features) A free [OpenRouter](https://openrouter.ai) API key
- (Optional, for "Continue with Google" login) A Google OAuth Client ID

---

## 4. Backend setup

```bash
cd food-delivery-app/backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in at least:
#   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
#   SECRET_KEY, JWT_SECRET_KEY (any long random strings)
# optional:
#   GOOGLE_CLIENT_ID                          (Google Sign-In)
#   RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET      (live payments)
#   AI_API_KEY / AI_MODEL / AI_BASE_URL        (AI assistant & recipe-to-order)
#   MAIL_HOST / MAIL_PORT / MAIL_USERNAME /
#   MAIL_PASSWORD / MAIL_FROM_EMAIL / MAIL_FROM_NAME,
#   FRONTEND_URL, EMAIL_ENABLED=1              (real password-reset emails — see section 7)
```

If no `DB_HOST`/`DB_USER` are set, the app falls back to a local SQLite file
(`backend/dev_fallback.db`) so it can boot without MySQL — useful for a quick look, but the schema
and migrations below target MySQL and are the supported path.

### Create the database schema

```bash
mysql -h <host> -u <user> -p < ../database/schema.sql
```

Then apply the migrations **in numeric order** to layer on the full feature set:

```bash
for f in ../database/migrations/*.sql; do
  mysql -h <host> -u <user> -p food_delivery < "$f"
done
```

Finally, seed reference data (states/cities, categories, GK question bank):

```bash
mysql -h <host> -u <user> -p food_delivery < ../database/seed.sql
```

### Seed admin + sample restaurants + sample food

This step also seeds states/categories/questions if you skipped the SQL files above (it's
idempotent — safe to run against a database that already has some of this data):

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
cp .env.example .env
# edit .env if needed (VITE_API_BASE, VITE_GOOGLE_CLIENT_ID)
npm run dev
```

Open `http://localhost:5173`.

For production build:

```bash
npm run build      # outputs to frontend/dist — serve with any static host / nginx
```

---

## 6. Logging in

- **Customer**: `http://localhost:5173/register` (OTP is simulated by default — see below), or
  "Continue with Google" if `VITE_GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_ID` are configured
- **Restaurant**: `http://localhost:5173/restaurant/login` (use a seeded account, or apply via
  `/restaurant/register` and approve it from the admin panel)
- **Admin**: `http://localhost:5173/admin/login` — this URL is intentionally not linked from the
  customer-facing navbar. Use the credentials printed by `seed_runner.py`.

### Seeded login credentials

These accounts are created automatically the first time you run
`python -m backend.utils.seed_runner` (see section 4). All restaurant accounts are seeded with
`status: approved`, so they can log in immediately without waiting on admin approval.

| Role       | Restaurant / Name    | Email                       | Password         |
|------------|-----------------------|------------------------------|-------------------|
| Admin      | Platform Admin        | `admin@fooddelivery.com`     | `Admin@123`       |
| Restaurant | Spice Villa           | `spicevilla@example.com`     | `Restaurant@123`  |
| Restaurant | Urban Bites           | `urbanbites@example.com`     | `Restaurant@123`  |
| Restaurant | The Curry House       | `curryhouse@example.com`     | `Restaurant@123`  |
| Restaurant | Green Leaf Kitchen    | `greenleaf@example.com`      | `Restaurant@123`  |

> ⚠️ These are **development-only** credentials meant for local testing. Change them (or delete
> these accounts and create your own) before deploying anywhere publicly reachable.

---

## 7. Integrations that need your own credentials

### OTP (mobile verification)
No SMS gateway is configured. In `OTP_DEBUG_MODE=1` (the default), the generated OTP code is
returned directly in the API response (`dev_otp` field) and shown in the UI so you can test the
full registration flow without a real SMS provider. **Before going live**, wire a real provider
(Twilio, MSG91, etc.) into `backend/services/otp_service.py` and set `OTP_DEBUG_MODE=0`.

### Password reset emails
Real email is sent from the backend over SMTP (`backend/services/email_service.py`) — nothing is
ever sent from React. By default `EMAIL_ENABLED=0`, so the backend logs what it *would* have sent
instead of making a real SMTP connection, letting you exercise the whole flow without any mail
credentials. Set `EMAIL_ENABLED=1` and fill in the `MAIL_*` variables below to send real emails.

**Setting up Gmail SMTP (recommended for testing/small deployments):**

1. Turn on **2-Step Verification** on the Google account you want to send from:
   [myaccount.google.com/security](https://myaccount.google.com/security).
2. Once 2-Step Verification is on, go to
   [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) and create an
   **App Password** (choose "Mail" / "Other", give it a name like "QuickBite backend"). Google
   gives you a 16-character code — copy it.
3. In `backend/.env`, set:
   ```
   MAIL_HOST=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=the-16-character-app-password   # NOT your normal Gmail password
   MAIL_FROM_EMAIL=your-email@gmail.com
   MAIL_FROM_NAME=QuickBite
   MAIL_USE_TLS=1
   MAIL_USE_SSL=0
   FRONTEND_URL=http://localhost:5173
   EMAIL_ENABLED=1
   ```
4. Never commit `backend/.env`, never put the App Password in `frontend/.env` or any Vite
   (`VITE_*`) variable, and never push it to GitHub. Only the Flask backend reads `MAIL_PASSWORD`.

Any other SMTP provider (SendGrid, Mailgun, Amazon SES, your company mail server, etc.) works the
same way — just point `MAIL_HOST` / `MAIL_PORT` at it and use its own username/password.

**Testing the flow end-to-end:**
1. `python app.py` (backend) and `npm run dev` (frontend).
2. Go to `/login` → **Forgot password?** → enter a real, registered customer email → **Send Reset
   Link**.
3. Check that inbox (and spam folder) for an email from `MAIL_FROM_NAME`.
4. Click **Reset Password** in the email — it opens `/reset-password?token=...` in the app.
5. Enter and confirm a new password, submit, and confirm you're redirected to `/login`.
6. Log in with the new password.

Also worth testing manually: an unregistered email (should get the same generic "if that email is
registered…" message), submitting the same email twice quickly (second request is silently
throttled by `PASSWORD_RESET_COOLDOWN_SECONDS`), an expired or already-used token, a Google-only
customer account (no email is sent — they keep using "Continue with Google"), and turning off wifi
to confirm SMTP failures return a generic error instead of a stack trace.

Reset tokens are never stored raw — only a SHA-256 hash is kept in `password_reset_tokens.token_hash`
— are single-use, expire after `PASSWORD_RESET_TOKEN_EXPIRY_MINUTES` (default 30), and are never
logged or returned by the API once `EMAIL_ENABLED=1`.

### Google Sign-In
Set the **same** `GOOGLE_CLIENT_ID` in both `backend/.env` and `frontend/.env`
(`VITE_GOOGLE_CLIENT_ID`). The Client Secret is never needed by this app — only the public Client
ID, used server-side to verify the token's audience. Leave it blank to keep the "Continue with
Google" button hidden.

### Razorpay
The backend creates orders and verifies payment signatures server-side
(`backend/routes/payment_routes.py`), and the secret key is never sent to the frontend. Until you
set `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` in your `.env`, choosing "Razorpay" at checkout
returns a clear "not configured" error rather than faking a successful payment. Get test keys from
your [Razorpay Dashboard](https://dashboard.razorpay.com/).

### AI Assistant / Recipe-to-Order
Uses an OpenAI-compatible `/chat/completions` endpoint via [OpenRouter](https://openrouter.ai) by
default (free tier, no credit card required). Set `AI_API_KEY` in `backend/.env`; `AI_MODEL` and
`AI_BASE_URL` have working defaults. The key is only ever read server-side.

---

## 8. Security notes

- Passwords are hashed with bcrypt; nowhere in the API (including admin customer views) is a
  password or password hash ever returned.
- JWT tokens carry `role`, and every sensitive backend route is decorated with
  `@token_required([...])` restricting it to specific roles — enforced server-side, not just
  hidden in the UI.
- Wallet balance checks and debits happen entirely server-side (`backend/services/wallet_service.py`);
  the client can never manipulate its own balance.
- GK game rewards are generated server-side after the game session completes, guarded by a unique
  constraint on `game_rewards.session_id` so a session can only ever pay out once.
- Restaurant food/order management endpoints verify the resource belongs to the authenticated
  restaurant before allowing edits — cross-restaurant tampering returns 404.
- A dedicated fraud-detection service and admin fraud center flag suspicious activity for review.

---

## 9. Extending further

This is a large, working v1 covering all core and advanced flows end-to-end. Natural next steps:
push/email notifications wired to a real provider, image uploads for food/restaurant photos
(currently URL-based), a production WSGI server (gunicorn) + reverse proxy in front of Flask, and
automated tests around the pricing/wallet/fraud services.
