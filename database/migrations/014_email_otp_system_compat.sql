-- ============================================================================
-- Migration 014 (compatibility version) — Real email OTP system
-- ============================================================================
-- Use this version if 014_email_otp_system.sql fails with error 1064 (your
-- MySQL doesn't support "ADD COLUMN IF NOT EXISTS" / "CREATE INDEX IF NOT
-- EXISTS"). Check what you already have first with:
--   DESCRIBE otp_verifications;
--   DESCRIBE customers;
-- and only run the ALTER lines for columns that are still missing.

ALTER TABLE otp_verifications
  MODIFY COLUMN mobile_number VARCHAR(15) NULL,
  MODIFY COLUMN otp_code VARCHAR(6) NULL,
  MODIFY COLUMN purpose VARCHAR(30) NOT NULL DEFAULT 'registration',
  ADD COLUMN email VARCHAR(150) NULL,
  ADD COLUMN otp_hash VARCHAR(64) NULL;

CREATE INDEX ix_otp_verifications_email
  ON otp_verifications (email);

ALTER TABLE customers
  ADD COLUMN email_verified TINYINT(1) NOT NULL DEFAULT 1;
