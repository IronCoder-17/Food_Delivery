-- ============================================================================
-- Migration 013 (compatibility version) — Real email delivery for password reset
-- ============================================================================
-- Use this version if your MySQL rejects "ADD COLUMN IF NOT EXISTS" (error
-- 1064). Confirmed columns needed based on: DESCRIBE password_reset_tokens;
-- showing only id, user_id, token, expires_at, used.
--
-- Safe to run once: only ADDs columns, never drops or rewrites existing
-- tables/rows. Existing tokens keep working because `token` is left in
-- place; new tokens issued after this migration store only a SHA-256 hash
-- in `token_hash` and leave `token` NULL.

ALTER TABLE password_reset_tokens
  MODIFY COLUMN token VARCHAR(255) NULL,
  ADD COLUMN token_hash VARCHAR(64) NULL UNIQUE,
  ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN requested_ip VARCHAR(64) NULL;

CREATE INDEX ix_password_reset_tokens_token_hash
  ON password_reset_tokens (token_hash);