-- ============================================================================
-- Migration 005 — Phase 3c: Referral System
-- ============================================================================
ALTER TABLE customers
  ADD COLUMN referral_code VARCHAR(30) NULL UNIQUE AFTER profile_image_url;

CREATE TABLE IF NOT EXISTS referral_configs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  referrer_points INT NOT NULL DEFAULT 100,
  referred_points INT NOT NULL DEFAULT 50,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS referrals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  referrer_customer_id INT NOT NULL,
  referred_customer_id INT NOT NULL UNIQUE,
  referral_code_used VARCHAR(30) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  qualifying_order_id INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  KEY idx_referral_referrer (referrer_customer_id),
  FOREIGN KEY (referrer_customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (referred_customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (qualifying_order_id) REFERENCES orders(id) ON DELETE SET NULL
);

-- New Authority permission key: customer.referrals