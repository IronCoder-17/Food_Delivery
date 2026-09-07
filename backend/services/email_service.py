"""
Reusable transactional email service for the Flask backend.

Sends real email over SMTP (works out of the box with Gmail SMTP + an App
Password, and with any other standard SMTP provider). All credentials are
read from environment variables via Flask's app config -- nothing here is
ever imported by, or exposed to, the React/Vite frontend.

Usage:
    from backend.services.email_service import send_email

    ok, error = send_email(
        to_email="customer@example.com",
        subject="Reset your password",
        html_body="<p>...</p>",
        text_body="...",
    )

When EMAIL_ENABLED=0 (the default in development), `send_email` does not
attempt any network call: it logs what *would* have been sent and returns
success, so the rest of the flow can be exercised locally without real SMTP
credentials. This is explicit and developer-friendly -- it never silently
pretends a real send happened when EMAIL_ENABLED=1.
"""

import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app


def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> tuple[bool, str | None]:
    """
    Send one email. Returns (success, error_message).

    On failure, `error_message` is a short, safe-to-log description --
    callers must NOT forward it to the end user (it may contain SMTP
    server responses). Never raises: SMTP/network failures are caught and
    reported via the return value so a mail outage can't turn into a 500
    for the customer.
    """
    cfg = current_app.config

    if not cfg.get("EMAIL_ENABLED"):
        current_app.logger.info(
            "[EMAIL_DISABLED] Would send email to=%s subject=%r (set EMAIL_ENABLED=1 "
            "and configure MAIL_* env vars to send real email).",
            to_email, subject,
        )
        return True, None

    host = cfg.get("MAIL_HOST")
    port = cfg.get("MAIL_PORT")
    username = cfg.get("MAIL_USERNAME")
    password = cfg.get("MAIL_PASSWORD")
    from_email = cfg.get("MAIL_FROM_EMAIL") or username
    from_name = cfg.get("MAIL_FROM_NAME") or "QuickBite"
    use_tls = cfg.get("MAIL_USE_TLS", True)
    use_ssl = cfg.get("MAIL_USE_SSL", False)

    if not host or not port or not from_email:
        # Misconfiguration, not a transient failure -- fail loudly in the
        # logs so a developer notices immediately, but never leak this
        # detail to the customer-facing response.
        current_app.logger.error(
            "Email is enabled (EMAIL_ENABLED=1) but MAIL_HOST/MAIL_PORT/MAIL_FROM_EMAIL "
            "are not fully configured. Check backend/.env."
        )
        return False, "Email is not configured."

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as server:
                if username and password:
                    server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                if username and password:
                    server.login(username, password)
                server.send_message(message)
        return True, None
    except smtplib.SMTPAuthenticationError:
        current_app.logger.exception(
            "SMTP authentication failed sending to %s. Check MAIL_USERNAME/MAIL_PASSWORD "
            "(for Gmail, MAIL_PASSWORD must be a 16-character App Password, not the normal "
            "account password).",
            to_email,
        )
        return False, "SMTP authentication failed."
    except (smtplib.SMTPException, OSError, TimeoutError):
        # Covers connection refused/timeouts, recipient refused, etc. The
        # full exception (with server response) goes to the backend log
        # only -- never to the API response.
        current_app.logger.exception("Failed to send email to %s.", to_email)
        return False, "Failed to send email."


def send_password_reset_email(*, to_email: str, customer_name: str, reset_url: str, expires_minutes: int) -> tuple[bool, str | None]:
    """Builds and sends the password-reset (link-based) email. Kept for
    backward compatibility / possible future use -- the current
    forgot-password flow uses send_otp_email() below instead."""
    from backend.services.email_templates import render_password_reset_email

    html_body, text_body = render_password_reset_email(
        customer_name=customer_name,
        reset_url=reset_url,
        expires_minutes=expires_minutes,
    )
    return send_email(
        to_email=to_email,
        subject="Reset your QuickBite password",
        html_body=html_body,
        text_body=text_body,
    )


def send_otp_email(to_email: str, otp: str, purpose: str, expires_minutes: int) -> tuple[bool, str | None]:
    """
    Builds and sends a one-time-password email for the given purpose
    (REGISTRATION, FORGOT_PASSWORD, LOGIN, EMAIL_VERIFICATION). The raw OTP
    is only ever passed in here and to the recipient's inbox -- callers
    must never log it or return it in an API response when EMAIL_ENABLED=1.
    """
    from backend.services.email_templates import render_otp_email, PURPOSE_HEADINGS

    html_body, text_body = render_otp_email(otp=otp, purpose=purpose, expires_minutes=expires_minutes)
    subject = f"Your QuickBite {PURPOSE_HEADINGS.get(purpose, 'verification code')}"
    return send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )
