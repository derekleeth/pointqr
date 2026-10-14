"""Async email sending service using aiosmtplib.

Email failures are caught and logged rather than re-raised so that a
misconfigured mail server never blocks a user-facing request.
"""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Core send helper
# ---------------------------------------------------------------------------

async def send_email(to: str, subject: str, html_body: str, text_body: str) -> None:
    """Send a multipart (plain-text + HTML) email asynchronously.

    Connects to the configured SMTP server, sends the message, and
    disconnects.  Any exception is caught and logged; callers are never
    notified of failures so that email errors don't break user-facing flows.

    Args:
        to:        Recipient email address.
        subject:   Email subject line.
        html_body: HTML version of the email body.
        text_body: Plain-text fallback for the email body.
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.mail_from
    message["To"] = to

    message.attach(MIMEText(text_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.mail_host,
            port=settings.mail_port,
            username=settings.mail_username or None,
            password=settings.mail_password or None,
            use_tls=settings.mail_ssl,
            start_tls=settings.mail_tls,
        )
        logger.info("Email sent to %s (subject: %r)", to, subject)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send email to %s (subject: %r)", to, subject)


# ---------------------------------------------------------------------------
# Shared HTML template helpers
# ---------------------------------------------------------------------------

_BASE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;overflow:hidden;
                      box-shadow:0 2px 8px rgba(0,0,0,.08);">
          <!-- Header -->
          <tr>
            <td style="background:#4f46e5;padding:28px 32px;">
              <span style="color:#ffffff;font-size:22px;font-weight:700;
                           letter-spacing:.5px;">PointQR</span>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px 32px 24px;">
              <h1 style="margin:0 0 16px;font-size:20px;color:#111827;">{heading}</h1>
              <p style="margin:0 0 24px;font-size:15px;color:#4b5563;line-height:1.6;">
                {body_text}
              </p>
              <a href="{action_url}"
                 style="display:inline-block;padding:12px 28px;background:#4f46e5;
                        color:#ffffff;text-decoration:none;border-radius:6px;
                        font-size:15px;font-weight:600;">
                {action_label}
              </a>
              <p style="margin:24px 0 0;font-size:13px;color:#6b7280;">
                If the button above doesn't work, copy and paste this URL into your browser:<br/>
                <a href="{action_url}" style="color:#4f46e5;word-break:break-all;">
                  {action_url}
                </a>
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 32px;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:12px;color:#9ca3af;">
                This link expires in {expiry_note}. If you didn't request this,
                you can safely ignore this email.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _render_html(
    subject: str,
    heading: str,
    body_text: str,
    action_url: str,
    action_label: str,
    expiry_note: str,
) -> str:
    """Render the shared HTML email template."""
    return _BASE_HTML.format(
        subject=subject,
        heading=heading,
        body_text=body_text,
        action_url=action_url,
        action_label=action_label,
        expiry_note=expiry_note,
    )


# ---------------------------------------------------------------------------
# Verification email
# ---------------------------------------------------------------------------

async def send_verification_email(to: str, token: str, frontend_url: str) -> None:
    """Send an email-address verification message to *to*.

    Args:
        to:           Recipient email address.
        token:        Signed JWT verification token.
        frontend_url: Base URL of the frontend (e.g. ``https://app.pointqr.dev``).
                      The link will be ``{frontend_url}/verify-email?token={token}``.
    """
    action_url = f"{frontend_url}/verify-email?token={token}"
    subject = "Verify your PointQR email address"
    heading = "Confirm your email address"
    body_text = (
        "Thanks for signing up for PointQR! Please verify your email address "
        "by clicking the button below. This link expires in 24 hours."
    )

    html_body = _render_html(
        subject=subject,
        heading=heading,
        body_text=body_text,
        action_url=action_url,
        action_label="Verify Email",
        expiry_note="24 hours",
    )
    text_body = (
        f"{heading}\n\n{body_text}\n\nVerify here: {action_url}\n\n"
        "If you didn't create an account you can ignore this email."
    )

    await send_email(to=to, subject=subject, html_body=html_body, text_body=text_body)


# ---------------------------------------------------------------------------
# Password-reset email
# ---------------------------------------------------------------------------

async def send_password_reset_email(to: str, token: str, frontend_url: str) -> None:
    """Send a password-reset link to *to*.

    Args:
        to:           Recipient email address.
        token:        Signed JWT password-reset token.
        frontend_url: Base URL of the frontend.
                      The link will be ``{frontend_url}/reset-password?token={token}``.
    """
    action_url = f"{frontend_url}/reset-password?token={token}"
    subject = "Reset your PointQR password"
    heading = "Reset your password"
    body_text = (
        "We received a request to reset the password for your PointQR account. "
        "Click the button below to choose a new password. This link expires in 30 minutes."
    )

    html_body = _render_html(
        subject=subject,
        heading=heading,
        body_text=body_text,
        action_url=action_url,
        action_label="Reset Password",
        expiry_note="30 minutes",
    )
    text_body = (
        f"{heading}\n\n{body_text}\n\nReset here: {action_url}\n\n"
        "If you did not request a password reset you can safely ignore this email."
    )

    await send_email(to=to, subject=subject, html_body=html_body, text_body=text_body)
