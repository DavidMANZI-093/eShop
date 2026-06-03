import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.shared.config import settings

_VERIFY_TTL_DISPLAY  = "24 hours"
_RESET_TTL_DISPLAY   = "1 hour"


def send_verification_email(to_address, token):
    url = f"{settings.BASE_URL}/auth/verify-email/{token}"
    _send(
        to_address=to_address,
        subject="Verify your eShop email address",
        html=_verification_html(url),
        plain=_verification_plain(url),
    )


def send_password_reset_email(to_address, token):
    url = f"{settings.BASE_URL}/auth/reset-password/{token}"
    _send(
        to_address=to_address,
        subject="Reset your eShop password",
        html=_reset_html(url),
        plain=_reset_plain(url),
    )


def _send(*, to_address, subject, html, plain):
    if not settings.MAIL_SERVER:
        _console_fallback(to_address, subject, plain)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.MAIL_FROM
    msg["To"]      = to_address
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))

    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
        if settings.MAIL_USE_TLS:
            smtp.starttls()
        smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        smtp.sendmail(settings.MAIL_FROM, to_address, msg.as_string())


def _console_fallback(to_address, subject, plain):
    separator = "-" * 60
    print(f"\n{separator}\n[DEV EMAIL] To: {to_address}\nSubject: {subject}\n\n{plain}\n{separator}\n")


# ── HTML email bodies ────────────────────────────────────────────────────────

def _email_wrapper(title, heading, body_html, cta_url, cta_label, footer_note):
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0f0f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f0f5;padding:40px 16px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:#080810;padding:24px 32px;text-align:center;">
            <span style="font-family:Georgia,serif;font-style:italic;font-size:28px;font-weight:700;color:#818cf8;">eShop</span>
          </td>
        </tr>
        <tr>
          <td style="background:#ffffff;padding:36px 32px;">
            <h1 style="margin:0 0 12px;font-size:22px;font-weight:600;color:#111118;line-height:1.3;">{heading}</h1>
            {body_html}
            <table cellpadding="0" cellspacing="0" style="margin:28px 0;">
              <tr>
                <td style="background:#6366f1;border-radius:8px;">
                  <a href="{cta_url}" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">{cta_label}</a>
                </td>
              </tr>
            </table>
            <p style="margin:0;font-size:13px;color:#888;line-height:1.6;">{footer_note}</p>
            <p style="margin:12px 0 0;font-size:12px;color:#aaa;">Or copy this link into your browser:<br>
              <span style="color:#6366f1;word-break:break-all;">{cta_url}</span>
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f9f9fb;border-top:1px solid #eee;padding:16px 32px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#aaa;">eShop &mdash; The marketplace for everyone</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _verification_html(url):
    return _email_wrapper(
        title="Verify your email",
        heading="Verify your email address",
        body_html="""
          <p style="margin:0 0 8px;font-size:15px;color:#444;line-height:1.7;">
            You&rsquo;re almost ready to start using eShop. Click the button below
            to confirm that this email address belongs to you.
          </p>""",
        cta_url=url,
        cta_label="Verify email address",
        footer_note=f"This link expires in {_VERIFY_TTL_DISPLAY}. "
                    "If you didn\u2019t create an eShop account you can safely ignore this email.",
    )


def _reset_html(url):
    return _email_wrapper(
        title="Reset your password",
        heading="Reset your password",
        body_html="""
          <p style="margin:0 0 8px;font-size:15px;color:#444;line-height:1.7;">
            We received a request to reset the password for your eShop account.
            Click the button below to choose a new password.
          </p>""",
        cta_url=url,
        cta_label="Reset my password",
        footer_note=f"This link expires in {_RESET_TTL_DISPLAY}. "
                    "If you didn\u2019t request a password reset your account is safe \u2014 "
                    "you can ignore this email.",
    )


# ── Plain text bodies ────────────────────────────────────────────────────────

def _verification_plain(url):
    return (
        f"Verify your eShop email address\n\n"
        f"Open the link below to verify your email address:\n{url}\n\n"
        f"This link expires in {_VERIFY_TTL_DISPLAY}.\n"
        "If you didn't create an eShop account you can ignore this email."
    )


def _reset_plain(url):
    return (
        f"Reset your eShop password\n\n"
        f"Open the link below to set a new password:\n{url}\n\n"
        f"This link expires in {_RESET_TTL_DISPLAY}.\n"
        "If you didn't request a reset your account is safe \u2014 ignore this email."
    )
