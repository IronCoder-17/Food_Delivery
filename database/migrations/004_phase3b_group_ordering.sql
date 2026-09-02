-- ============================================================================
-- Migration 004 — Phase 3b: Group Ordering
-- ============================================================================
CREATE TABLE IF NOT EXISTS group_orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  host_customer_id INT NOT NULL,
  restaurant_id INT NOT NULL,
  invite_code VARCHAR(20) NOT NULL UNIQUE,
  deadline DATETIME NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  created_order_id INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_group_order_host (host_customer_id),
  KEY idx_group_order_code (invite_code),
  FOREIGN KEY (host_customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (created_order_id) REFERENCES orders(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS group_order_members (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_order_id INT NOT NULL,
  customer_id INT NOT NULL,
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_group_member (group_order_id, customer_id),
  KEY idx_group_member_customer (customer_id),
  FOREIGN KEY (group_order_id) REFERENCES group_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS group_order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_order_id INT NOT NULL,
  customer_id INT NOT NULL,
  food_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_group_item_order (group_order_id),
  KEY idx_group_item_customer (customer_id),
  FOREIGN KEY (group_order_id) REFERENCES group_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);

-- New Authority permission key: customer.group_ordering
