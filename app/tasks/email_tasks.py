from __future__ import annotations

import logging

from app.tasks.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="email.send_notification")
def send_email_notification(to: str, subject: str, body: str) -> None:
    """Simulated email sender.

    In production, integrate with a real email provider (SES, SendGrid, etc.).
    """

    logger.info("Sending email", extra={"to": to, "subject": subject})
    # Here we'd call the real email API

