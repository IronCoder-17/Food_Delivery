-- ============================================================================
-- Migration 003 — Phase 3a: AI Meal Planner
-- ============================================================================
CREATE TABLE IF NOT EXISTS meal_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  restaurant_id INT NULL,
  days INT NOT NULL,
  meals_per_day INT NOT NULL,
  budget DECIMAL(10,2) NULL,
  is_veg TINYINT(1) NULL,
  max_spend_per_meal DECIMAL(10,2) NULL,
  estimated_total DECIMAL(10,2) NOT NULL DEFAULT 0,
  summary_note TEXT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_meal_plan_customer (customer_id),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS meal_plan_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  meal_plan_id INT NOT NULL,
  day_index INT NOT NULL,
  meal_index INT NOT NULL,
  meal_label VARCHAR(30) NOT NULL,
  food_id INT NULL,
  quantity INT NOT NULL DEFAULT 1,
  price_at_planning DECIMAL(10,2) NULL,
  unavailable_reason VARCHAR(150) NULL,
  KEY idx_meal_plan_item_plan (meal_plan_id),
  FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE SET NULL
);

-- New Authority permission key: customer.meal_planner
