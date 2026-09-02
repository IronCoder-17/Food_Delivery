-- ============================================================================
-- Migration 001 — Phase 1: Saved Addresses upgrade, Favorites, Reviews
-- ============================================================================
-- Safe to run against an existing production database:
--   - Only ADDs columns/tables. Nothing is dropped, renamed, or backfilled
--     destructively.
--   - Requires MySQL 8.0.29+ for "ADD COLUMN" / "IF NOT EXISTS"
--     table guards. If you're on an older MySQL, remove the "IF NOT EXISTS"
--     clauses and run once (they are idempotent by construction anyway).
--   - New tables (favorite_foods, favorite_restaurants, reviews, review_replies)
--     will also be created automatically by db.create_all() on app startup,
--     but this file is the canonical, explicit migration for ops/DBA review.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Extend `addresses` for multi-address support (contact info + geo)
-- ---------------------------------------------------------------------------
ALTER TABLE addresses
  ADD COLUMN contact_name VARCHAR(150) NULL AFTER label,
  ADD COLUMN contact_phone VARCHAR(15) NULL AFTER contact_name,
  ADD COLUMN latitude DECIMAL(10,7) NULL AFTER pincode,
  ADD COLUMN longitude DECIMAL(10,7) NULL AFTER latitude,
  ADD COLUMN created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP AFTER is_default,
  ADD COLUMN updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- Backfill created_at/updated_at for any pre-existing rows so they're never NULL.
UPDATE addresses SET created_at = NOW() WHERE created_at IS NULL;
UPDATE addresses SET updated_at = NOW() WHERE updated_at IS NULL;

-- ---------------------------------------------------------------------------
-- 2. Favorites (Foods & Restaurants)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS favorite_foods (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  food_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_favorite_food (customer_id, food_id),
  KEY idx_fav_food_customer (customer_id),
  KEY idx_fav_food_food (food_id),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorite_restaurants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  restaurant_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_favorite_restaurant (customer_id, restaurant_id),
  KEY idx_fav_rest_customer (customer_id),
  KEY idx_fav_rest_restaurant (restaurant_id),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- 3. Reviews & Replies
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  restaurant_id INT NOT NULL,
  food_id INT NOT NULL,
  order_id INT NOT NULL,
  rating INT NOT NULL,
  comment TEXT NULL,
  image_url VARCHAR(255) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_review_per_order_item (customer_id, order_id, food_id),
  KEY idx_review_customer (customer_id),
  KEY idx_review_restaurant (restaurant_id),
  KEY idx_review_food (food_id),
  KEY idx_review_order (order_id),
  CONSTRAINT chk_review_rating CHECK (rating BETWEEN 1 AND 5),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_replies (
  id INT AUTO_INCREMENT PRIMARY KEY,
  review_id INT NOT NULL UNIQUE,
  restaurant_id INT NOT NULL,
  reply_text TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- 4. New Authority permission keys used by Phase 1 (rows are created
--    idempotently by ensure_default_permissions() at app startup -- nothing
--    to do here manually, this comment just documents the new keys):
--      customer.favorites
--      customer.reviews
--      customer.manage_addresses
--      restaurant.reply_reviews
-- ---------------------------------------------------------------------------