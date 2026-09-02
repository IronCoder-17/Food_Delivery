-- ============================================================
-- Food Delivery App - MySQL Schema
-- Run against MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS food_delivery
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_delivery;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- Locations
-- ------------------------------------------------------------
CREATE TABLE states (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE cities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  state_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  FOREIGN KEY (state_id) REFERENCES states(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_city_per_state (state_id, name)
);

-- ------------------------------------------------------------
-- Users (base identity for all 3 roles; role-specific detail
-- tables hold role-only fields)
-- ------------------------------------------------------------
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role ENUM('customer','restaurant','admin') NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE customers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  first_name VARCHAR(80) NOT NULL,
  last_name VARCHAR(80) NOT NULL,
  mobile_number VARCHAR(15) NOT NULL UNIQUE,
  mobile_verified TINYINT(1) NOT NULL DEFAULT 0,
  state_id INT,
  city_id INT,
  address TEXT,
  pincode VARCHAR(10),
  date_of_birth DATE NULL,
  gender VARCHAR(20) NULL,
  profile_image_url VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  google_id VARCHAR(255) NULL UNIQUE,
  auth_provider VARCHAR(20) NOT NULL DEFAULT 'local',
  profile_completed TINYINT(1) NOT NULL DEFAULT 1,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (state_id) REFERENCES states(id),
  FOREIGN KEY (city_id) REFERENCES cities(id)
);

-- If you already have an existing database created from an older version of
-- this schema, run this instead of recreating the table:
-- ALTER TABLE customers
--   ADD COLUMN date_of_birth DATE NULL,
--   ADD COLUMN gender VARCHAR(20) NULL,
--   ADD COLUMN profile_image_url VARCHAR(255) NULL;
--
-- Google Sign-In support (see database/migrations/010_google_oauth_customer_login.sql):
-- ALTER TABLE customers
--   ADD COLUMN google_id VARCHAR(255) NULL UNIQUE,
--   ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'local',
--   ADD COLUMN profile_completed TINYINT(1) NOT NULL DEFAULT 1;

CREATE TABLE addresses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  label VARCHAR(50) DEFAULT 'Home',
  address TEXT NOT NULL,
  state_id INT,
  city_id INT,
  pincode VARCHAR(10),
  delivery_instruction VARCHAR(20) NOT NULL DEFAULT 'ring_bell',
  is_default TINYINT(1) DEFAULT 0,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (state_id) REFERENCES states(id),
  FOREIGN KEY (city_id) REFERENCES cities(id)
);

CREATE TABLE restaurants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  restaurant_name VARCHAR(150) NOT NULL,
  owner_name VARCHAR(120) NOT NULL,
  mobile_number VARCHAR(15) NOT NULL,
  address TEXT NOT NULL,
  state_id INT,
  city_id INT,
  pincode VARCHAR(10),
  description TEXT,
  logo_url VARCHAR(255),
  cover_image_url VARCHAR(255),
  document_url VARCHAR(255),
  opening_time TIME,
  closing_time TIME,
  status ENUM('pending','approved','rejected','deactivated') NOT NULL DEFAULT 'pending',
  rating DECIMAL(3,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (state_id) REFERENCES states(id),
  FOREIGN KEY (city_id) REFERENCES cities(id)
);

CREATE TABLE admins (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- OTP
-- ------------------------------------------------------------
CREATE TABLE otp_verifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  mobile_number VARCHAR(15) NOT NULL,
  otp_code VARCHAR(6) NOT NULL,
  purpose ENUM('registration','password_reset') NOT NULL DEFAULT 'registration',
  attempts INT NOT NULL DEFAULT 0,
  is_verified TINYINT(1) NOT NULL DEFAULT 0,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE password_reset_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  used TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Categories & Foods
-- ------------------------------------------------------------
CREATE TABLE categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  image_url VARCHAR(255),
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE foods (
  id INT AUTO_INCREMENT PRIMARY KEY,
  restaurant_id INT NOT NULL,
  category_id INT NOT NULL,
  name VARCHAR(150) NOT NULL,
  is_veg TINYINT(1) NOT NULL DEFAULT 1,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  discount_percent DECIMAL(5,2) NOT NULL DEFAULT 0,
  image_url VARCHAR(255),
  preparation_time_minutes INT DEFAULT 20,
  is_available TINYINT(1) NOT NULL DEFAULT 1,
  rating DECIMAL(3,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES categories(id),
  INDEX idx_food_category (category_id),
  INDEX idx_food_restaurant (restaurant_id)
);

-- ------------------------------------------------------------
-- Cart
-- ------------------------------------------------------------
CREATE TABLE carts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL UNIQUE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE cart_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cart_id INT NOT NULL,
  food_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_cart_food (cart_id, food_id)
);

-- ------------------------------------------------------------
-- Orders
-- ------------------------------------------------------------
CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  restaurant_id INT NOT NULL,
  address_text TEXT NOT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  delivery_fee DECIMAL(10,2) NOT NULL DEFAULT 0,
  total_amount DECIMAL(10,2) NOT NULL,
  payment_method ENUM('razorpay','cod','wallet') NOT NULL,
  payment_status ENUM('pending','paid','failed') NOT NULL DEFAULT 'pending',
  order_status ENUM('placed','accepted','preparing','ready','out_for_delivery','delivered','cancelled') NOT NULL DEFAULT 'placed',
  delivery_instruction VARCHAR(20) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
  INDEX idx_order_customer (customer_id),
  INDEX idx_order_restaurant (restaurant_id)
);

CREATE TABLE order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  food_id INT NOT NULL,
  food_name VARCHAR(150) NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  quantity INT NOT NULL,
  line_total DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id)
);

-- ------------------------------------------------------------
-- Payments
-- ------------------------------------------------------------
CREATE TABLE payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  method ENUM('razorpay','cod','wallet') NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  status ENUM('pending','success','failed') NOT NULL DEFAULT 'pending',
  razorpay_order_id VARCHAR(100),
  razorpay_payment_id VARCHAR(100),
  razorpay_signature VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Wallet
-- ------------------------------------------------------------
CREATE TABLE wallets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL UNIQUE,
  balance DECIMAL(10,2) NOT NULL DEFAULT 0,
  total_credits DECIMAL(10,2) NOT NULL DEFAULT 0,
  total_debits DECIMAL(10,2) NOT NULL DEFAULT 0,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE wallet_transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  wallet_id INT NOT NULL,
  type ENUM('credit','debit','bonus') NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  reason VARCHAR(150) NOT NULL,
  reference_type ENUM('order','game_reward','manual') NOT NULL,
  reference_id INT,
  balance_after DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- GK Game
-- ------------------------------------------------------------
CREATE TABLE game_questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question TEXT NOT NULL,
  option_a VARCHAR(255) NOT NULL,
  option_b VARCHAR(255) NOT NULL,
  option_c VARCHAR(255) NOT NULL,
  option_d VARCHAR(255) NOT NULL,
  correct_option ENUM('A','B','C','D') NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE game_sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  status ENUM('in_progress','completed') NOT NULL DEFAULT 'in_progress',
  correct_count INT DEFAULT 0,
  score INT DEFAULT 0,
  reward_amount DECIMAL(10,2) DEFAULT 0,
  reward_claimed TINYINT(1) NOT NULL DEFAULT 0,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE game_session_questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  session_id INT NOT NULL,
  question_id INT NOT NULL,
  position INT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES game_questions(id)
);

CREATE TABLE game_answers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  session_id INT NOT NULL,
  question_id INT NOT NULL,
  selected_option ENUM('A','B','C','D','TIMEOUT') NOT NULL,
  is_correct TINYINT(1) NOT NULL DEFAULT 0,
  answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES game_questions(id)
);

CREATE TABLE game_rewards (
  id INT AUTO_INCREMENT PRIMARY KEY,
  session_id INT NOT NULL UNIQUE,
  customer_id INT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  wallet_transaction_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Notifications
-- ------------------------------------------------------------
CREATE TABLE notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recipient_role ENUM('customer','restaurant','admin') NOT NULL,
  recipient_id INT NOT NULL,   -- id in customers/restaurants/admins table
  title VARCHAR(150) NOT NULL,
  message VARCHAR(500) NOT NULL,
  is_read TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_notif_recipient (recipient_role, recipient_id)
);

-- ------------------------------------------------------------
-- Loyalty system
-- ------------------------------------------------------------
CREATE TABLE loyalty_levels (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE,
  rank_order INT NOT NULL UNIQUE,
  minimum_points INT NOT NULL,
  maximum_points INT NULL,        -- NULL = unbounded (top rank)
  benefits TEXT,
  description TEXT,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE customer_loyalty (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL UNIQUE,
  points INT NOT NULL DEFAULT 0,
  lifetime_points INT NOT NULL DEFAULT 0,
  rank VARCHAR(30) NOT NULL DEFAULT 'Bronze',
  total_orders INT NOT NULL DEFAULT 0,
  total_spending DECIMAL(12,2) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE loyalty_transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  points INT NOT NULL,             -- positive = earned, negative = deducted
  transaction_type VARCHAR(20) NOT NULL,   -- earn/redeem/admin_add/admin_remove/reversal
  reference_type VARCHAR(30),      -- order/manual/refund
  reference_id INT,
  description VARCHAR(255),
  admin_id INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (admin_id) REFERENCES admins(id),
  UNIQUE KEY uq_loyalty_txn_reference (reference_type, reference_id, transaction_type),
  INDEX idx_loyalty_txn_customer (customer_id)
);

-- ------------------------------------------------------------
-- Authority (permission) management
-- ------------------------------------------------------------
CREATE TABLE authority_permissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  permission_key VARCHAR(60) NOT NULL UNIQUE,
  permission_name VARCHAR(120) NOT NULL,
  user_type ENUM('customer','restaurant') NOT NULL,
  description VARCHAR(255),
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  default_allowed TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE user_authorities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,            -- customers.id or restaurants.id (per user_type)
  user_type ENUM('customer','restaurant') NOT NULL,
  permission_id INT NOT NULL,
  is_allowed TINYINT(1) NOT NULL DEFAULT 1,
  updated_by INT NULL,             -- admins.id
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (permission_id) REFERENCES authority_permissions(id) ON DELETE CASCADE,
  FOREIGN KEY (updated_by) REFERENCES admins(id),
  UNIQUE KEY uq_user_permission (user_id, user_type, permission_id),
  INDEX idx_user_authorities_user (user_id, user_type)
);

CREATE TABLE authority_audit_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  admin_id INT NULL,
  user_id INT NOT NULL,
  user_type ENUM('customer','restaurant') NOT NULL,
  permission VARCHAR(60) NOT NULL,
  previous_status TINYINT(1) NOT NULL,
  new_status TINYINT(1) NOT NULL,
  reason VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_id) REFERENCES admins(id)
);

-- ------------------------------------------------------------
-- AI Assistant usage log
-- ------------------------------------------------------------
CREATE TABLE ai_conversation_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  message TEXT NOT NULL,
  response TEXT,
  error VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  INDEX idx_ai_log_customer (customer_id)
);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- Batch 1 Feature Upgrade (see database/migrations/011_batch1_features.sql
-- for the safe ALTER/CREATE-IF-NOT-EXISTS version for an existing database)
-- ============================================================================

CREATE TABLE food_moods (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  emoji VARCHAR(10) NOT NULL DEFAULT '🍽️',
  is_active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE food_mood_mapping (
  food_id INT NOT NULL,
  mood_id INT NOT NULL,
  PRIMARY KEY (food_id, mood_id),
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  FOREIGN KEY (mood_id) REFERENCES food_moods(id) ON DELETE CASCADE,
  INDEX idx_mood_mapping_mood (mood_id)
);

CREATE TABLE food_allergens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  is_active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE food_allergen_mapping (
  food_id INT NOT NULL,
  allergen_id INT NOT NULL,
  PRIMARY KEY (food_id, allergen_id),
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  FOREIGN KEY (allergen_id) REFERENCES food_allergens(id) ON DELETE CASCADE,
  INDEX idx_allergen_mapping_allergen (allergen_id)
);

CREATE TABLE restaurant_kitchen_status (
  restaurant_id INT PRIMARY KEY,
  status VARCHAR(20) NOT NULL DEFAULT 'normal',
  extra_minutes INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE chef_specials (
  id INT AUTO_INCREMENT PRIMARY KEY,
  restaurant_id INT NOT NULL,
  food_id INT NOT NULL,
  special_price DECIMAL(10,2) NOT NULL,
  quantity_total INT NOT NULL,
  quantity_sold INT NOT NULL DEFAULT 0,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  description TEXT,
  image_url VARCHAR(255),
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  INDEX idx_chef_special_restaurant (restaurant_id),
  INDEX idx_chef_special_window (start_time, end_time)
);

CREATE TABLE food_streaks (
  customer_id INT PRIMARY KEY,
  current_streak INT NOT NULL DEFAULT 0,
  best_streak INT NOT NULL DEFAULT 0,
  streak_points INT NOT NULL DEFAULT 0,
  last_activity_date DATE NULL,
  last_milestone_awarded INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

INSERT IGNORE INTO food_moods (name, emoji) VALUES
  ('Comfort Food', '🍲'), ('Post-Workout', '💪'), ('Light & Healthy', '🥗'),
  ('Spicy Craving', '🌶️'), ('Sweet Craving', '🍰'), ('Quick Bite', '⚡'),
  ('Late Night', '🌙'), ('Family Meal', '👨‍👩‍👧‍👦'), ('Budget Friendly', '💰'),
  ('Energy Boost', '🔋');

INSERT IGNORE INTO food_allergens (name) VALUES
  ('Vegan'), ('Jain'), ('Nut-free'), ('Dairy-free'), ('Gluten-free'),
  ('Contains Nuts'), ('Contains Dairy'), ('Contains Gluten'), ('Spicy');

-- ============================================================================
-- Batch 2/3 Feature Upgrade (see database/migrations/012_batch2_features.sql
-- for the safe ALTER/CREATE-IF-NOT-EXISTS version for an existing database)
-- ============================================================================

ALTER TABLE group_orders ADD COLUMN enable_voting TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE group_orders ADD COLUMN voting_deadline DATETIME NULL;
ALTER TABLE group_orders ADD COLUMN max_participants INT NULL;
ALTER TABLE group_orders ADD COLUMN budget DECIMAL(10,2) NULL;

CREATE TABLE group_order_suggestions (
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

CREATE TABLE group_order_votes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  suggestion_id INT NOT NULL,
  customer_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (suggestion_id) REFERENCES group_order_suggestions(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  UNIQUE KEY uq_one_vote_per_member (suggestion_id, customer_id)
);

CREATE TABLE group_order_payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_order_id INT NOT NULL,
  customer_id INT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  split_type VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  paid_at DATETIME NULL,
  FOREIGN KEY (group_order_id) REFERENCES group_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  UNIQUE KEY uq_one_share_per_member (group_order_id, customer_id),
  INDEX idx_group_payment_group (group_order_id)
);

CREATE TABLE surplus_deals (
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

CREATE TABLE order_packing_proofs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL UNIQUE,
  image_path VARCHAR(255) NOT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

ALTER TABLE orders ADD COLUMN tip_amount DECIMAL(10,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN eco_delivery TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN donation_amount DECIMAL(10,2) NOT NULL DEFAULT 0;

ALTER TABLE foods ADD COLUMN calories INT NULL;
ALTER TABLE foods ADD COLUMN protein_grams DECIMAL(6,2) NULL;
ALTER TABLE foods ADD COLUMN carbs_grams DECIMAL(6,2) NULL;
ALTER TABLE foods ADD COLUMN fat_grams DECIMAL(6,2) NULL;

CREATE TABLE nutrition_logs (
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

-- If you already have an existing database, run
-- database/migrations/012_batch2_features.sql instead, which uses safe
-- ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS guards.
-- (For the Batch 1 tables/columns above this section, use
-- database/migrations/011_batch1_features.sql the same way.)
