-- ============================================================================
-- Migration 009 — Phase 5b/c/d: Fraud Detection, Promotion A/B Testing,
--                                 Dispute Resolution
-- ============================================================================

CREATE TABLE IF NOT EXISTS fraud_flags (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  rule VARCHAR(60) NOT NULL,
  reason VARCHAR(255) NOT NULL,
  incident_count INT NOT NULL DEFAULT 1,
  risk_score INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'review',
  reviewed_by_admin_id INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_fraud_customer (customer_id),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (reviewed_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS promotion_experiments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  variant_a_label VARCHAR(100) DEFAULT 'Promotion A',
  variant_b_label VARCHAR(100) DEFAULT 'Promotion B',
  discount_percent_a DECIMAL(5,2) NOT NULL DEFAULT 0,
  discount_percent_b DECIMAL(5,2) NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  start_date DATETIME NULL,
  end_date DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS promotion_assignments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  experiment_id INT NOT NULL,
  customer_id INT NOT NULL,
  variant VARCHAR(1) NOT NULL,
  assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_promo_assignment (experiment_id, customer_id),
  KEY idx_promo_assignment_experiment (experiment_id),
  FOREIGN KEY (experiment_id) REFERENCES promotion_experiments(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

ALTER TABLE orders
  ADD COLUMN promotion_assignment_id INT NULL AFTER delivery_longitude,
  ADD CONSTRAINT fk_orders_promotion_assignment FOREIGN KEY (promotion_assignment_id)
    REFERENCES promotion_assignments(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS dispute_tickets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  customer_id INT NOT NULL,
  restaurant_id INT NOT NULL,
  reason VARCHAR(30) NOT NULL,
  description TEXT NULL,
  evidence_url VARCHAR(255) NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'open',
  resolution_note TEXT NULL,
  refund_amount DECIMAL(10,2) NULL,
  resolved_by_admin_id INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_dispute_order (order_id),
  KEY idx_dispute_customer (customer_id),
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
  FOREIGN KEY (resolved_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS dispute_events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  dispute_id INT NOT NULL,
  actor_type VARCHAR(20) NOT NULL,
  actor_id INT NULL,
  event_type VARCHAR(30) NOT NULL,
  note TEXT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_dispute_event_dispute (dispute_id),
  FOREIGN KEY (dispute_id) REFERENCES dispute_tickets(id) ON DELETE CASCADE
);

-- New Authority permission key: customer.disputes