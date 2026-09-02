-- ============================================================================
-- Migration 008 — Phase 5a: Order location snapshot (foundation for Heatmap)
-- ============================================================================
ALTER TABLE orders
  ADD COLUMN delivery_city_id INT NULL AFTER address_text,
  ADD COLUMN delivery_pincode VARCHAR(10) NULL AFTER delivery_city_id,
  ADD COLUMN delivery_latitude DECIMAL(10,7) NULL AFTER delivery_pincode,
  ADD COLUMN delivery_longitude DECIMAL(10,7) NULL AFTER delivery_latitude,
  ADD CONSTRAINT fk_orders_delivery_city FOREIGN KEY (delivery_city_id) REFERENCES cities(id) ON DELETE SET NULL;

-- Historical orders and any order placed with a freely-typed (non-saved)
-- address will have NULL here -- this is intentional honesty, not a bug:
-- we do not retroactively geocode or guess locations we were never given.