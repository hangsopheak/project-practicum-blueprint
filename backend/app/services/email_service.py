import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import EmailOTP, User, Profile
from app.core.security import create_access_token

logger = logging.getLogger("jobmatch.email_service")

OTP_EXPIRE_MINUTES = 10


def generate_otp_code() -> str:
    """Generate a secure 6-digit numeric OTP code."""
    return str(secrets.randbelow(900000) + 100000)


def send_email_otp(
    db: Session,
    email: str,
    purpose: str = "login_or_verify"
) -> Tuple[EmailOTP, str]:
    """
    Generate an OTP code, save it in the database, and dispatch it via email
    (or log to console in development mode).
    """
    # Invalidate any previously unused OTPs for this email and purpose
    db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.purpose == purpose,
        EmailOTP.is_used == False
    ).update({"is_used": True})

    code = generate_otp_code()
    now_utc = datetime.now(timezone.utc)
    expires_at = now_utc + timedelta(minutes=OTP_EXPIRE_MINUTES)

    otp_record = EmailOTP(
        email=email,
        code=code,
        purpose=purpose,
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    # Dispatch email (or fallback to development logging)
    _dispatch_email(email=email, code=code, purpose=purpose)

    return otp_record, code


def verify_email_otp(
    db: Session,
    email: str,
    code: str,
    purpose: str = "login_or_verify"
) -> Tuple[bool, Optional[User], Optional[str], str]:
    """
    Verify the provided OTP code.
    Returns: (is_valid, user_object_if_any, access_token_if_any, message)
    """
    now_utc = datetime.now(timezone.utc)

    # Find the most recent active OTP for this email and purpose
    otp = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.purpose == purpose,
        EmailOTP.is_used == False
    ).order_by(desc(EmailOTP.created_at)).first()

    if not otp:
        return False, None, None, "No active OTP request found for this email"

    if otp.code != code.strip():
        return False, None, None, "Invalid verification code"

    # Normalize expires_at for comparison
    exp = otp.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now_utc > exp:
        otp.is_used = True
        db.commit()
        return False, None, None, "Verification code has expired"

    # Mark as used
    otp.is_used = True

    # Check if a user exists with this email
    user = db.query(User).filter(User.email == email).first()
    access_token = None

    if user:
        access_token = create_access_token(subject=str(user.id))
    else:
        # Automatically create user on first verified OTP login if preferred
        new_user = User(
            email=email,
            password_hash="OTP_VERIFIED_NO_PASSWORD",
            role="user"
        )
        db.add(new_user)
        db.flush()

        default_profile = Profile(
            user_id=new_user.id,
            full_name=email.split("@")[0].capitalize(),
            experience_level="entry",
            preferred_role="Candidate",
            preferred_location="Phnom Penh"
        )
        db.add(default_profile)
        user = new_user
        access_token = create_access_token(subject=str(new_user.id))

    db.commit()
    db.refresh(user)

    return True, user, access_token, "OTP verified successfully"


from app.core.config import settings


def _build_html_template(code: str, email: str, purpose: str) -> str:
    """Generate a clean, modern, responsive HTML email template for OTP delivery."""
    purpose_label = "Account Verification"
    if purpose == "login":
        purpose_label = "Instant Sign-In"
    elif purpose == "reset":
        purpose_label = "Password Reset"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JobMatch Verification Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f1f5f9; padding: 40px 15px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04); border: 1px solid #e2e8f0;" cellspacing="0" cellpadding="0">
          
          <!-- Gradient Top Accent Bar -->
          <tr>
            <td style="height: 6px; background: linear-gradient(90deg, #2563eb 0%, #3b82f6 50%, #06b6d4 100%);"></td>
          </tr>

          <!-- Header Section with Logo -->
          <tr>
            <td style="padding: 32px 36px 16px 36px; text-align: center;">
              <div style="text-align: center; margin-bottom: 12px;">
                <img src="cid:jobmatch_logo" alt="JobMatch Cambodia" width="80" height="80" style="width: 80px; height: 80px; display: inline-block; object-fit: contain; margin: 0 auto;" />
              </div>
              <div style="display: inline-block; padding: 4px 14px; background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 9999px; margin-bottom: 12px;">
                <span style="font-size: 12px; font-weight: 700; color: #1d4ed8; letter-spacing: 0.5px; text-transform: uppercase;">
                  🇰🇭 JobMatch Cambodia
                </span>
              </div>
              <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;">
                {purpose_label}
              </h1>
              <p style="margin: 0; font-size: 14px; color: #64748b; line-height: 1.5;">
                We received a request to access your candidate account. Use the code below to complete your verification.
              </p>
            </td>
          </tr>

          <!-- OTP Code Display Card -->
          <tr>
            <td style="padding: 10px 36px 24px 36px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); border: 2px dashed #cbd5e1; border-radius: 12px; text-align: center;">
                <tr>
                  <td style="padding: 24px 16px;">
                    <span style="display: block; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                      Your One-Time Code
                    </span>
                    <span style="display: inline-block; font-size: 38px; font-weight: 800; color: #1e40af; letter-spacing: 8px; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;">
                      {code}
                    </span>
                    <div style="margin-top: 10px;">
                      <span style="display: inline-block; font-size: 12px; font-weight: 600; color: #b45309; background-color: #fef3c7; border: 1px solid #fde68a; padding: 4px 10px; border-radius: 6px;">
                        ⏱️ Expires in {OTP_EXPIRE_MINUTES} minutes
                      </span>
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Security Notice -->
          <tr>
            <td style="padding: 0 36px 28px 36px;">
              <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; padding: 12px 16px;">
                <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.5;">
                  <strong>Security Note:</strong> Never share this code with anyone. JobMatch team members will never ask for your verification code.
                </p>
              </div>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding: 0 36px;">
              <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 0;">
            </td>
          </tr>

          <!-- Footer Section -->
          <tr>
            <td style="padding: 24px 36px 32px 36px; text-align: center;">
              <p style="margin: 0 0 6px 0; font-size: 12px; color: #94a3b8;">
                This message was sent to <strong style="color: #64748b;">{email}</strong>
              </p>
              <p style="margin: 0 0 12px 0; font-size: 12px; color: #94a3b8;">
                If you did not request this verification, you can safely ignore this email.
              </p>
              <p style="margin: 0; font-size: 11px; color: #cbd5e1; font-weight: 500;">
                © 2026 JobMatch Cambodia • Phnom Penh, Cambodia • AI-Powered Job Aggregator
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _dispatch_email(email: str, code: str, purpose: str) -> None:
    """
    Send an email via SMTP if enabled; otherwise log to console for development/demo.
    """
    subject = f"Your JobMatch Verification Code: {code}"
    plain_text_body = (
        f"JobMatch Cambodia Verification\n\n"
        f"Your 6-digit verification code is: {code}\n"
        f"This code will expire in {OTP_EXPIRE_MINUTES} minutes.\n\n"
        f"If you did not request this code, please ignore this email.\n\n"
        f"— JobMatch Cambodia Team"
    )
    html_body = _build_html_template(code=code, email=email, purpose=purpose)

    # Always log for local development and defense demonstrations
    logger.info(f"📧 [EMAIL OTP] Verification Code for {email}: {code} (Valid for {OTP_EXPIRE_MINUTES} mins, Purpose: {purpose})")
    print(
        f"\n=======================================================\n"
        f"📧 [EMAIL OTP DISPATCH]\n"
        f"To:      {email}\n"
        f"Code:    {code}\n"
        f"Purpose: {purpose}\n"
        f"Expires: {OTP_EXPIRE_MINUTES} minutes\n"
        f"=======================================================\n",
        flush=True,
    )

    if settings.SMTP_ENABLED and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            # Root message is multipart/related to hold both alternative text/html and inline CID image
            msg = MIMEMultipart("related")
            msg["From"] = f"JobMatch Cambodia <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
            msg["To"] = email
            msg["Subject"] = subject

            # Alternative container for plain text vs HTML
            alt_part = MIMEMultipart("alternative")
            alt_part.attach(MIMEText(plain_text_body, "plain", "utf-8"))
            alt_part.attach(MIMEText(html_body, "html", "utf-8"))
            msg.attach(alt_part)

            # Attach inline logo with Content-ID <jobmatch_logo>
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static/logo.png"))
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-ID", "<jobmatch_logo>")
                    img.add_header("Content-Disposition", "inline", filename="logo.png")
                    msg.attach(img)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info(f"✅ [EMAIL OTP] Live rich HTML email with logo delivered to {email}")
        except Exception as e:
            logger.warning(f"⚠️ [EMAIL OTP] SMTP delivery failed ({e}), fell back to console log.")
