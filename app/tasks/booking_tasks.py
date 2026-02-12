from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.db.session import AsyncSessionFactory
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.tasks.worker import celery_app
from app.tasks.email_tasks import send_email_notification


logger = logging.getLogger(__name__)


async def _get_booking(booking_id: UUID) -> Booking | None:
    async with AsyncSessionFactory() as session:
        return await session.get(Booking, booking_id)


@celery_app.task(name="booking.send_created_email")
def send_booking_created_email(booking_id: str) -> None:
    """Send confirmation emails when a booking is created."""

    async def _inner() -> None:
        booking = await _get_booking(UUID(booking_id))
        if not booking:
            return
        # In a real system, we would join to user emails; for now we log.
        logger.info(
            "Booking created",
            extra={
                "booking_id": str(booking.id),
                "item_id": str(booking.item_id),
                "renter_id": str(booking.renter_id),
                "owner_id": str(booking.owner_id),
            },
        )

    asyncio.run(_inner())


@celery_app.task(name="booking.send_start_reminder")
def send_booking_start_reminder(booking_id: str) -> None:
    """Reminder shortly before a booking becomes active."""

    async def _inner() -> None:
        booking = await _get_booking(UUID(booking_id))
        if not booking or booking.status not in (BookingStatus.APPROVED, BookingStatus.ACTIVE):
            return
        logger.info(
            "Booking reminder",
            extra={
                "booking_id": str(booking.id),
                "start_date": booking.start_date.isoformat(),
            },
        )

    asyncio.run(_inner())


@celery_app.task(name="booking.auto_release_deposit")
def auto_release_deposit(booking_id: str) -> None:
    """Automatically release deposit after a delay if booking is completed and no disputes."""

    async def _inner() -> None:
        booking = await _get_booking(UUID(booking_id))
        if not booking or booking.status != BookingStatus.COMPLETED:
            return

        if booking.escrow_record and booking.escrow_record.amount_released == 0:
            # Simulate auto-release; in a real system we'd call EscrowService
            logger.info(
                "Auto-releasing deposit",
                extra={
                    "booking_id": str(booking.id),
                    "escrow_id": str(booking.escrow_record.id),
                },
            )

    asyncio.run(_inner())

