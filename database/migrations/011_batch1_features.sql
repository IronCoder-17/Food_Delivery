-- ============================================================================
-- Migration 011 — Batch 1 Feature Upgrade
-- Mood-Based Ordering, Ingredient & Allergen Tags, Delivery Preferences,
-- Live Kitchen Load, Chef's Specials, Food Streaks.
--
-- (Order Again / Reorder already existed in this codebase -- see
-- backend/routes/reorder_routes.py -- so no schema change was needed for it.)
--
-- Safe to run once on an existing database: only ADDs tables/columns, never
-- drops or rewrites existing data. Requires MySQL 8.0.29+ for
-- "ADD COLUMN"; on older MySQL, remove those clauses.
-- ============================================================================

-- Force this session onto a utf8mb4 connection before inserting the emoji
-- below. Without this, a client whose default connection charset is latin1
-- (the MySQL default) will mangle the emoji bytes on INSERT even though the
-- destination column and this file are both proper UTF-8 ("mojibake").
-- Always import this file with, e.g.:
--   mysql --default-character-set=utf8mb4 -u root -p food_delivery < 011_batch1_features.sql
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 1. Mood-Based Ordering
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_moods (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  emoji VARCHAR(10) NOT NULL DEFAULT '🍽️',
  is_active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS food_mood_mapping (
  food_id INT NOT NULL,
  mood_id INT NOT NULL,
  PRIMARY KEY (food_id, mood_id),
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  FOREIGN KEY (mood_id) REFERENCES food_moods(id) ON DELETE CASCADE,
  INDEX idx_mood_mapping_mood (mood_id)
);

INSERT IGNORE INTO food_moods (name, emoji) VALUES
  ('Comfort Food', '🍲'), ('Post-Workout', '💪'), ('Light & Healthy', '🥗'),
  ('Spicy Craving', '🌶️'), ('Sweet Craving', '🍰'), ('Quick Bite', '⚡'),
  ('Late Night', '🌙'), ('Family Meal', '👨‍👩‍👧‍👦'), ('Budget Friendly', '💰'),
  ('Energy Boost', '🔋');

-- ---------------------------------------------------------------------------
-- 2. Ingredient & Allergen Tags
-- (Vegetarian/Non-Veg already exists as foods.is_veg -- not duplicated here.)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_allergens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  is_active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS food_allergen_mapping (
  food_id INT NOT NULL,
  allergen_id INT NOT NULL,
  PRIMARY KEY (food_id, allergen_id),
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  FOREIGN KEY (allergen_id) REFERENCES food_allergens(id) ON DELETE CASCADE,
  INDEX idx_allergen_mapping_allergen (allergen_id)
);

INSERT IGNORE INTO food_allergens (name) VALUES
  ('Vegan'), ('Jain'), ('Nut-free'), ('Dairy-free'), ('Gluten-free'),
  ('Contains Nuts'), ('Contains Dairy'), ('Contains Gluten'), ('Spicy');

-- ---------------------------------------------------------------------------
-- 3. Delivery Preferences
-- ---------------------------------------------------------------------------
ALTER TABLE addresses
  ADD COLUMN delivery_instruction VARCHAR(20) NOT NULL DEFAULT 'ring_bell';

-- Snapshot of the chosen instruction at the time of THIS order (an address's
-- default can change later -- the order should keep what was true then).
ALTER TABLE orders
  ADD COLUMN delivery_instruction VARCHAR(20) NULL;

-- ---------------------------------------------------------------------------
-- 4. Live Kitchen Load
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS restaurant_kitchen_status (
  restaurant_id INT PRIMARY KEY,
  status VARCHAR(20) NOT NULL DEFAULT 'normal',
  extra_minutes INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- 5. Chef's Specials
-- (Deliberately a separate table from flash_sales -- Chef's Special has its
-- own semantics: an explicit special_price + limited quantity + its own
-- description/image, rather than a percent-off an existing listing.)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chef_specials (
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

-- ---------------------------------------------------------------------------
-- 6. Food Streaks
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_streaks (
  customer_id INT PRIMARY KEY,
  current_streak INT NOT NULL DEFAULT 0,
  best_streak INT NOT NULL DEFAULT 0,
  streak_points INT NOT NULL DEFAULT 0,
  last_activity_date DATE NULL,
  last_milestone_awarded INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);