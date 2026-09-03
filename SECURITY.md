# Security Policy

## Supported Versions

This project is actively maintained on the `main` branch. Only the latest commit on `main` receives security fixes.

| Branch      | Supported          |
| ----------- | ------------------ |
| `main`      | :white_check_mark: |
| older forks | :x:                 |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

- **Do not** open a public GitHub issue for security vulnerabilities.
- Instead, report it privately via [GitHub Security Advisories](../../security/advisories/new) or by contacting the maintainer directly.
- Please include steps to reproduce, potential impact, and any suggested fix if available.

You can expect an initial response within **3-5 days**. Confirmed vulnerabilities will be patched as soon as possible, and credit will be given in the release notes (unless you prefer to remain anonymous).

## Security Measures Already in Place

- Passwords are hashed using **bcrypt** — never stored or returned in plaintext.
- Authentication uses **JWT tokens** with role-based access control enforced on the backend (not just hidden in the UI).
- Payment verification (Razorpay) is handled **server-side**, and secret keys are never exposed to the frontend.
- Wallet balance checks and debits happen entirely server-side to prevent client-side tampering.
- Sensitive routes are protected by role-specific middleware (`@token_required`).

## Known Limitations (Development Setup)

- OTP verification and password reset currently run in **debug mode** (`OTP_DEBUG_MODE=1`) with no real SMS/email provider wired in — intended for local development/testing only.
- Before deploying to production, rotate all default/seeded credentials and configure real OTP/email providers.
