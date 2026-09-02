-- ============================================================================
-- Migration 006 — Phase 4a: Live Order Tracking (real event timeline)
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_tracking_events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  status VARCHAR(30) NOT NULL,
  note VARCHAR(255) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_tracking_order (order_id),
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Note: this migration does not backfill tracking_events for orders placed
-- before this feature existed -- those orders will show an empty timeline
-- (accurate: we genuinely don't know their historical transition times)
-- rather than fabricating retroactive event timestamps.
