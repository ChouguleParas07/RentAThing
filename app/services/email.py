import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

def send_verification_email(email: str, code: str):
    settings = get_settings()
    
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP credentials not set. Skipping verification email.")
        return None

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your email address - STASHLY"
        msg["From"] = f"STASHLY <{settings.smtp_user}>"
        msg["To"] = email

        html_content = f"""
        <html>
            <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Welcome to STASHLY!</h2>
                <p>Thanks for signing up. Please verify your email address to get started.</p>
                <div style="margin: 30px 0;">
                    <p style="font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #333; background: #f4f4f4; padding: 10px; display: inline-block; border-radius: 4px;">
                        {code}
                    </p>
                </div>
                <p>Enter this 6-digit code on the verification page.</p>
                <p>This code will expire in 10 minutes.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))

        # Connect to Gmail SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            # Remove spaces from the app password if there are any
            password = settings.smtp_password.replace(" ", "")
            server.login(settings.smtp_user, password)
            server.send_message(msg)
            
        logger.info(f"Verification email sent to {email} via Gmail SMTP")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        return None
