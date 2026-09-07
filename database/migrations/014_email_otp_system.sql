-- ============================================================================
-- Migration 014 — Real email OTP system (registration + forgot password)
-- ============================================================================
-- Adds email-OTP support to the existing `otp_verifications` table (reused,
-- not duplicated) and an `email_verified` flag on `customers`. Only ADDs
-- columns / relaxes NOT NULL constraints -- never drops or rewrites
-- existing rows, so all existing mobile-OTP rows, customers, and orders are
-- preserved untouched.
--
-- NOTE: If your MySQL version rejects "ADD COLUMN IF NOT EXISTS" (error
-- 1064 -- this affects MySQL < 8.0.29), use
-- 014_email_otp_system_compat.sql instead, which has the same effect
-- without that syntax.

ALTER TABLE otp_verifications
  MODIFY COLUMN mobile_number VARCHAR(15) NULL,
  MODIFY COLUMN otp_code VARCHAR(6) NULL,
  -- Widen from ENUM('registration','password_reset') to VARCHAR so new
  -- purpose values (REGISTRATION, FORGOT_PASSWORD, etc.) can be stored
  -- without truncation/errors. Existing values are preserved as-is.
  MODIFY COLUMN purpose VARCHAR(30) NOT NULL DEFAULT 'registration',
  ADD COLUMN IF NOT EXISTS email VARCHAR(150) NULL,
  ADD COLUMN IF NOT EXISTS otp_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS ix_otp_verifications_email
  ON otp_verifications (email);

ALTER TABLE customers
  ADD COLUMN IF NOT EXISTS email_verified TINYINT(1) NOT NULL DEFAULT 1;
