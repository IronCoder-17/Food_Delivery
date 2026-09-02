-- ============================================================================
-- Migration 010 — Google Sign-In for Customer Login (compatibility version)
-- ============================================================================
-- Use this version if your MySQL is older than 8.0.29 and rejects
-- "ADD COLUMN IF NOT EXISTS" (error 1064 near "IF NOT EXISTS").
--
-- Safe to run once on an existing database: only ADDs columns, never drops
-- or rewrites existing tables/rows. All existing email/password customers
-- get auth_provider='local' and profile_completed=1 (they already have
-- complete profiles), so their login behavior is unchanged.
--
-- IMPORTANT: If you already partially ran the other version of this
-- migration and some columns exist, running this one again will fail with
-- "Duplicate column name". In that case, run only the ADD COLUMN lines for
-- whichever columns are still missing (check with: DESCRIBE customers;).

ALTER TABLE customers
  ADD COLUMN google_id VARCHAR(255) NULL UNIQUE,
  ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'local',
  ADD COLUMN profile_completed TINYINT(1) NOT NULL DEFAULT 1;

-- Backfill, in case your MySQL version applied the DEFAULT only to new rows.
UPDATE customers SET auth_provider = 'local' WHERE auth_provider IS NULL;
UPDATE customers SET profile_completed = 1 WHERE profile_completed IS NULL;