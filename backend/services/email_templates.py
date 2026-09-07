"""
Email markup for transactional emails. Kept separate from email_service.py
so the SMTP plumbing and the message content can change independently.
"""

from html import escape

BRAND_NAME = "QuickBite"
BRAND_COLOR = "#E4602A"
BRAND_COLOR_DARK = "#C94F1F"
SUPPORT_EMAIL = "support@quickbite.example.com"


PURPOSE_HEADINGS = {
    "REGISTRATION": "Email Verification Code",
    "EMAIL_VERIFICATION": "Email Verification Code",
    "FORGOT_PASSWORD": "Password Reset Verification Code",
    "LOGIN": "Login Verification Code",
}


def render_otp_email(*, otp: str, purpose: str, expires_minutes: int) -> tuple[str, str]:
    """Returns (html_body, text_body) for a one-time-password email."""
    heading = PURPOSE_HEADINGS.get(purpose, "Your Verification Code")
    safe_otp = escape(otp)

    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{heading}</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#ffffff;border-radius:12px;overflow:hidden;">
          <tr>
            <td style="background-color:{BRAND_COLOR};padding:28px 32px;text-align:center;">
              <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:0.3px;">{BRAND_NAME}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 8px 32px;">
              <h1 style="margin:0 0 20px 0;font-size:20px;color:#1a1a1a;">{heading}</h1>
              <p style="margin:0 0 20px 0;font-size:15px;line-height:1.6;color:#333333;">
                Use the code below to continue. It's only valid for {expires_minutes} minutes.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px 32px;text-align:center;">
              <div style="display:inline-block;background-color:#fbeee7;border:1px dashed {BRAND_COLOR};
                          border-radius:10px;padding:16px 32px;">
                <span style="font-size:32px;font-weight:700;letter-spacing:8px;color:{BRAND_COLOR_DARK};">{safe_otp}</span>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 32px 32px;border-top:1px solid #eeeeee;">
              <p style="margin:20px 0 0 0;font-size:13px;line-height:1.6;color:#666666;">
                If you did not request this code, you can safely ignore this email.
              </p>
              <p style="margin:12px 0 0 0;font-size:13px;line-height:1.6;color:#666666;">
                For your security, never share this code with anyone -- {BRAND_NAME} staff will never ask for it.
              </p>
              <p style="margin:20px 0 0 0;font-size:12px;line-height:1.6;color:#999999;">
                Need help? Contact us at
                <a href="mailto:{SUPPORT_EMAIL}" style="color:{BRAND_COLOR_DARK};">{SUPPORT_EMAIL}</a>.
              </p>
            </td>
          </tr>
        </table>
        <p style="margin:16px 0 0 0;font-size:11px;color:#999999;">&copy; {BRAND_NAME}. All rights reserved.</p>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    text_body = f"""\
{BRAND_NAME} - {heading}

Your verification code is: {otp}

This code will expire in {expires_minutes} minutes.

If you did not request this code, you can safely ignore this email.

For your security, never share this code with anyone -- {BRAND_NAME} staff will never ask for it.

Need help? Contact us at {SUPPORT_EMAIL}
"""
    return html_body, text_body


def render_password_reset_email(*, customer_name: str, reset_url: str, expires_minutes: int) -> tuple[str, str]:
    """Returns (html_body, text_body) for the password-reset email."""
    safe_name = escape(customer_name or "there")
    safe_url = escape(reset_url, quote=True)

    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reset your password</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#ffffff;border-radius:12px;overflow:hidden;">
          <tr>
            <td style="background-color:{BRAND_COLOR};padding:28px 32px;text-align:center;">
              <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:0.3px;">{BRAND_NAME}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 8px 32px;">
              <h1 style="margin:0 0 16px 0;font-size:20px;color:#1a1a1a;">Reset Your Password</h1>
              <p style="margin:0 0 8px 0;font-size:15px;line-height:1.6;color:#333333;">Hi {safe_name},</p>
              <p style="margin:0 0 24px 0;font-size:15px;line-height:1.6;color:#333333;">
                We received a request to reset the password for your {BRAND_NAME} account.
                Click the button below to choose a new password.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px 32px;text-align:center;">
              <a href="{safe_url}"
                 style="display:inline-block;background-color:{BRAND_COLOR};color:#ffffff;text-decoration:none;
                        font-size:15px;font-weight:700;padding:14px 32px;border-radius:8px;">
                Reset Password
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 8px 32px;">
              <p style="margin:0 0 16px 0;font-size:13px;line-height:1.6;color:#666666;">
                This link will expire in {expires_minutes} minutes. If the button above doesn't work,
                copy and paste this URL into your browser:
              </p>
              <p style="margin:0 0 24px 0;font-size:12px;line-height:1.5;color:{BRAND_COLOR_DARK};word-break:break-all;">
                {safe_url}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 32px 32px;border-top:1px solid #eeeeee;">
              <p style="margin:20px 0 0 0;font-size:13px;line-height:1.6;color:#666666;">
                If you did not request a password reset, you can safely ignore this email --
                your password will not be changed.
              </p>
              <p style="margin:12px 0 0 0;font-size:13px;line-height:1.6;color:#666666;">
                For your security, never share this link with anyone.
              </p>
              <p style="margin:20px 0 0 0;font-size:12px;line-height:1.6;color:#999999;">
                Need help? Contact us at
                <a href="mailto:{SUPPORT_EMAIL}" style="color:{BRAND_COLOR_DARK};">{SUPPORT_EMAIL}</a>.
              </p>
            </td>
          </tr>
        </table>
        <p style="margin:16px 0 0 0;font-size:11px;color:#999999;">&copy; {BRAND_NAME}. All rights reserved.</p>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    text_body = f"""\
{BRAND_NAME} - Reset Your Password

Hi {customer_name or "there"},

We received a request to reset the password for your {BRAND_NAME} account.

Reset your password using this link (expires in {expires_minutes} minutes):
{reset_url}

If you did not request a password reset, you can safely ignore this email --
your password will not be changed.

For your security, never share this link with anyone.

Need help? Contact us at {SUPPORT_EMAIL}
"""
    return html_body, text_body
