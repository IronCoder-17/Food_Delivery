-- ============================================================================
-- Migration 007 — Phase 4b/c/d: QuickBite Pass, Restaurant Subscriptions,
--                                 Sponsored Restaurants
-- ============================================================================

-- ---------------------------------------------------------------------------
-- QuickBite Pass
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pass_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  duration_days INT NOT NULL,
  min_order_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  max_free_deliveries_per_period INT NOT NULL DEFAULT 4,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pass_plan_restaurants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plan_id INT NOT NULL,
  restaurant_id INT NOT NULL,
  KEY idx_pass_plan_restaurant_plan (plan_id),
  FOREIGN KEY (plan_id) REFERENCES pass_plans(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quickbite_passes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  plan_id INT NOT NULL,
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  current_period_index INT NOT NULL DEFAULT 0,
  deliveries_used_in_period INT NOT NULL DEFAULT 0,
  KEY idx_pass_customer (customer_id),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (plan_id) REFERENCES pass_plans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS delivery_benefit_usage (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL UNIQUE,
  customer_id INT NOT NULL,
  pass_id INT NOT NULL,
  discount_amount DECIMAL(10,2) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (pass_id) REFERENCES quickbite_passes(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- Restaurant Subscription Plans
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscription_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  duration_days INT NOT NULL,
  description TEXT NULL,
  granted_permissions TEXT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS restaurant_subscriptions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  restaurant_id INT NOT NULL,
  plan_id INT NOT NULL,
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  activated_by_admin_id INT NULL,
  KEY idx_restaurant_sub_restaurant (restaurant_id),
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE CASCADE,
  FOREIGN KEY (activated_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------------
-- Sponsored / Featured Restaurants
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sponsored_campaigns (
  id INT AUTO_INCREMENT PRIMARY KEY,
  restaurant_id INT NOT NULL,
  placement VARCHAR(50) NOT NULL DEFAULT 'homepage',
  priority INT NOT NULL DEFAULT 0,
  budget DECIMAL(10,2) NULL,
  campaign_start DATETIME NOT NULL,
  campaign_end DATETIME NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_sponsored_restaurant (restaurant_id),
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- New Authority permission keys:
--   customer.quickbite_pass
--   restaurant.advanced_analytics, restaurant.promotional_tools, restaurant.sponsored_eligible
--   (the latter three default to DENIED -- only granted via an active subscription)
