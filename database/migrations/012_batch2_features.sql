-- ============================================================================
-- Migration 012 — Batch 2/3 Feature Upgrade
-- Group Order Voting + Bill Splitting, Surplus Deals, Packing Photo Proof,
-- Eco Delivery, Dynamic Tipping, Micro-Donations, Nutrition Tracking,
-- Recipe-to-Order.
--
-- Safe to run once on an existing database: only ADDs tables/columns, never
-- drops or rewrites existing data. Requires MySQL 8.0.29+ for
-- "ADD COLUMN"; on older MySQL, remove those clauses.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Group Order Voting + config
-- ---------------------------------------------------------------------------
ALTER TABLE group_orders
  ADD COLUMN enable_voting TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN voting_deadline DATETIME NULL,
  ADD COLUMN max_participants INT NULL,
  ADD COLUMN budget DECIMAL(10,2) NULL;

CREATE TABLE IF NOT EXISTS group_order_suggestions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_order_id INT NOT NULL,
  food_id INT NOT NULL,
  suggested_by_customer_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (group_order_id) REFERENCES group_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  FOREIGN KEY (suggested_by_customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  UNIQUE KEY uq_group_suggestion (group_order_id, food_id),
  INDEX idx_suggestion_group (group_order_id)
);

CREATE TABLE IF NOT EXISTS group_order_votes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  suggestion_id INT NOT NULL,
  customer_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (suggestion_id) REFERENCES group_order_suggestions(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  UNIQUE KEY uq_one_vote_per_member (suggestion_id, customer_id)
);

-- ---------------------------------------------------------------------------
-- 2. Group Bill Splitting (real reimbursement via the app's own Wallet --
-- see backend/services/group_bill_service.py for why this is the honest,
-- non-fake design instead of simulating external UPI).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_order_payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_order_id INT NOT NULL,
  customer_id INT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  split_type VARCHAR(20) NOT NULL, -- equal / item_based
  status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending/paid/failed/refunded
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  paid_at DATETIME NULL,
  FOREIGN KEY (group_order_id) REFERENCES group_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  UNIQUE KEY uq_one_share_per_member (group_order_id, customer_id),
  INDEX idx_group_payment_group (group_order_id)
);

-- ---------------------------------------------------------------------------
-- 3. Leftover / Surplus Food Deals
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS surplus_deals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  restaurant_id INT NOT NULL,
  food_id INT NOT NULL,
  original_price DECIMAL(10,2) NOT NULL,
  discount_price DECIMAL(10,2) NOT NULL,
  quantity_total INT NOT NULL,
  quantity_sold INT NOT NULL DEFAULT 0,
  order_deadline DATETIME NOT NULL,
  expiry_time DATETIME NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  INDEX idx_surplus_restaurant (restaurant_id),
  INDEX idx_surplus_window (order_deadline, expiry_time)
);

-- ---------------------------------------------------------------------------
-- 4. Packing Photo Proof
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_packing_proofs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL UNIQUE,
  image_path VARCHAR(255) NOT NULL, -- server filesystem path, NEVER a public URL
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- 5. Delivery Tipping + Eco Delivery (stored per order)
-- ---------------------------------------------------------------------------
ALTER TABLE orders
  ADD COLUMN tip_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN eco_delivery TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN donation_amount DECIMAL(10,2) NOT NULL DEFAULT 0;

-- ---------------------------------------------------------------------------
-- 6. Nutrition Tracking (restaurant-provided, per food)
-- ---------------------------------------------------------------------------
ALTER TABLE foods
  ADD COLUMN calories INT NULL,
  ADD COLUMN protein_grams DECIMAL(6,2) NULL,
  ADD COLUMN carbs_grams DECIMAL(6,2) NULL,
  ADD COLUMN fat_grams DECIMAL(6,2) NULL;

CREATE TABLE IF NOT EXISTS nutrition_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_id INT NOT NULL,
  calories INT NOT NULL DEFAULT 0,
  protein_grams DECIMAL(6,2) NOT NULL DEFAULT 0,
  carbs_grams DECIMAL(6,2) NOT NULL DEFAULT 0,
  fat_grams DECIMAL(6,2) NOT NULL DEFAULT 0,
  logged_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  UNIQUE KEY uq_one_log_per_order (customer_id, order_id),
  INDEX idx_nutrition_customer_date (customer_id, logged_date)
);