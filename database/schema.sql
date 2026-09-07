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
  email_verified TINYINT(1) NOT NULL DEFAULT 1,
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
  -- Mobile-SMS OTP fields (existing, unchanged behavior) -- nullable so
  -- email-based rows below don't need a mobile number.
  mobile_number VARCHAR(15) NULL,
  otp_code VARCHAR(6) NULL,
  -- Email OTP fields (new). Only otp_hash is ever stored for these rows --
  -- the raw 6-digit code exists only in the email sent to the customer and
  -- briefly in memory on the backend while verifying.
  email VARCHAR(150) NULL,
  otp_hash VARCHAR(64) NULL,
  -- VARCHAR (not ENUM) so new purposes (REGISTRATION, FORGOT_PASSWORD,
  -- LOGIN, EMAIL_VERIFICATION) can be added without a schema change.
  purpose VARCHAR(30) NOT NULL DEFAULT 'registration',
  attempts INT NOT NULL DEFAULT 0,
  is_verified TINYINT(1) NOT NULL DEFAULT 0,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_otp_verifications_email (email)
);

CREATE TABLE password_reset_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  -- Raw token column kept only for backward compatibility with pre-existing
  -- rows from older deployments; new rows leave this NULL and use
  -- token_hash instead so the raw token is never persisted.
  token VARCHAR(255) NULL UNIQUE,
  token_hash VARCHAR(64) NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  used TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  requested_ip VARCHAR(64) NULL,
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
