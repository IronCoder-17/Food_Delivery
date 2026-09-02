-- ============================================================================
-- Migration 002 — Phase 2: Inventory/Sold-Out, Combos, Flash Sales,
--                            One-Tap Reorder, Scheduled Orders
-- ============================================================================
-- Additive only. Requires MySQL 8.0.29+ for "ADD COLUMN".
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Inventory / Sold-Out fields on foods
-- ---------------------------------------------------------------------------
ALTER TABLE foods
  ADD COLUMN track_inventory TINYINT(1) NOT NULL DEFAULT 0 AFTER rating,
  ADD COLUMN stock_quantity INT NULL AFTER track_inventory,
  ADD COLUMN low_stock_threshold INT NOT NULL DEFAULT 5 AFTER stock_quantity;

-- ---------------------------------------------------------------------------
-- 2. Combos / Bundles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS combos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  restaurant_id INT NOT NULL,
  name VARCHAR(150) NOT NULL,
  description TEXT NULL,
  combo_price DECIMAL(10,2) NOT NULL,
  image_url VARCHAR(255) NULL,
  start_date DATETIME NULL,
  end_date DATETIME NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_combo_restaurant (restaurant_id),
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS combo_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  combo_id INT NOT NULL,
  food_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  KEY idx_combo_item_combo (combo_id),
  FOREIGN KEY (combo_id) REFERENCES combos(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- 3. Flash Sales
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flash_sales (
  id INT AUTO_INCREMENT PRIMARY KEY,
  restaurant_id INT NOT NULL,
  food_id INT NULL,
  combo_id INT NULL,
  discount_percent DECIMAL(5,2) NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  max_quantity INT NULL,
  sold_quantity INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_flash_restaurant (restaurant_id),
  KEY idx_flash_food (food_id),
  KEY idx_flash_combo (combo_id),
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
  FOREIGN KEY (combo_id) REFERENCES combos(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- 4. Cart / Order support for combos (nullable food_id, new combo_id column)
-- ---------------------------------------------------------------------------
ALTER TABLE cart_items
  MODIFY COLUMN food_id INT NULL,
  ADD COLUMN combo_id INT NULL AFTER food_id,
  ADD CONSTRAINT fk_cart_items_combo FOREIGN KEY (combo_id) REFERENCES combos(id) ON DELETE CASCADE;

ALTER TABLE order_items
  MODIFY COLUMN food_id INT NULL,
  ADD COLUMN combo_id INT NULL AFTER food_id,
  ADD CONSTRAINT fk_order_items_combo FOREIGN KEY (combo_id) REFERENCES combos(id) ON DELETE CASCADE;

-- ---------------------------------------------------------------------------
-- 5. Scheduled Orders
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scheduled_orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  restaurant_id INT NOT NULL,
  address_text TEXT NOT NULL,
  payment_method VARCHAR(20) NOT NULL,
  scheduled_for DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
  failure_reason VARCHAR(255) NULL,
  created_order_id INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_scheduled_customer (customer_id),
  KEY idx_scheduled_for (scheduled_for),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (created_order_id) REFERENCES orders(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS scheduled_order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  scheduled_order_id INT NOT NULL,
  food_id INT NOT NULL,
  quantity INT NOT NULL,
  KEY idx_scheduled_item_order (scheduled_order_id),
  FOREIGN KEY (scheduled_order_id) REFERENCES scheduled_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- 6. New Authority permission keys used by Phase 2 (rows created idempotently
--    by ensure_default_permissions() at app startup -- documented here only):
--      customer.reorder
--      customer.scheduled_orders
--      restaurant.manage_combos
--      restaurant.manage_flash_sales
--      restaurant.manage_inventory
-- ---------------------------------------------------------------------------