from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import BookingStatus, UserRole
from app.models.item import Item
from app.repositories.booking_repository import BookingRepository
from app.repositories.item_repository import ItemRepository
from app.schemas.booking import BookingCreate, BookingListResponse, BookingRead
from app.services.escrow_service import EscrowService


class BookingService:
    """Business logic for bookings and availability."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.bookings = BookingRepository(db)
        self.items = ItemRepository(db)
        self.escrow = EscrowService(db)

    async def _validate_item_available(
        self,
        item: Item,
        start_date,
        end_date,
    ) -> None:
        if not item.is_active:
            raise ValueError("Item is not active")

        if item.available_from and start_date < item.available_from:
            raise ValueError("Start date is before item availability")

        if item.available_until and end_date > item.available_until:
            raise ValueError("End date is after item availability")

        if await self.bookings.has_overlapping_booking(
            item_id=item.id,
            start_date=start_date,
            end_date=end_date,
        ):
            raise ValueError("Item is already booked for the selected dates")

    async def create_booking(
        self,
        renter_id: UUID,
        payload: BookingCreate,
    ) -> BookingRead:
        item = await self.items.get_by_id(payload.item_id)
        if not item:
            raise ValueError("Item not found")

        if item.owner_id == renter_id:
            raise PermissionError("Owners cannot book their own items")

        await self._validate_item_available(item, payload.start_date, payload.end_date)

        # Simple pricing calculation; we will refine with discounts later
        nights = (payload.end_date - payload.start_date).days or 1
        total_price = item.daily_price * nights

        booking = await self.bookings.create(
            item_id=item.id,
            renter_id=renter_id,
            owner_id=item.owner_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            total_price=total_price,
            notes=payload.notes,
        )

        # Immediately hold the security deposit in simulated escrow
        if item.security_deposit > 0:
            await self.escrow.create_and_hold_for_booking(
                booking_id=booking.id,
                renter_id=renter_id,
                owner_id=item.owner_id,
                item_id=item.id,
                amount_held=item.security_deposit,
            )
        else:
            await self.db.commit()
            await self.db.refresh(booking)

        return BookingRead.model_validate(booking)

    async def list_bookings_for_renter(
        self,
        renter_id: UUID,
        skip: int,
        limit: int,
    ) -> BookingListResponse:
        total, bookings = await self.bookings.list_for_renter(renter_id=renter_id, skip=skip, limit=limit)
        return BookingListResponse(
            total=total,
            bookings=[BookingRead.model_validate(b) for b in bookings],
        )

    async def list_bookings_for_owner(
        self,
        owner_id: UUID,
        skip: int,
        limit: int,
    ) -> BookingListResponse:
        total, bookings = await self.bookings.list_for_owner(owner_id=owner_id, skip=skip, limit=limit)
        return BookingListResponse(
            total=total,
            bookings=[BookingRead.model_validate(b) for b in bookings],
        )

    async def _ensure_actor_can_modify(
        self,
        *,
        booking,
        actor_id: UUID,
        role: UserRole,
    ) -> None:
        if role == UserRole.ADMIN:
            return
        if actor_id not in (booking.renter_id, booking.owner_id):
            raise PermissionError("You are not part of this booking")

    async def update_status(
        self,
        *,
        booking_id: UUID,
        actor_id: UUID,
        role: UserRole,
        new_status: BookingStatus,
    ) -> BookingRead:
        booking = await self.bookings.get_by_id(booking_id)
        if not booking:
            raise LookupError("Booking not found")

        await self._ensure_actor_can_modify(booking=booking, actor_id=actor_id, role=role)

        # Basic lifecycle guards
        if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
            raise ValueError("Booking is already finalized")

        if booking.status == BookingStatus.REQUESTED and new_status not in (
            BookingStatus.APPROVED,
            BookingStatus.CANCELLED,
        ):
            raise ValueError("Requested bookings can only be approved or cancelled")

        if booking.status == BookingStatus.APPROVED and new_status not in (
            BookingStatus.ACTIVE,
            BookingStatus.CANCELLED,
        ):
            raise ValueError("Approved bookings can only become active or cancelled")

        if booking.status == BookingStatus.ACTIVE and new_status not in (BookingStatus.COMPLETED,):
            raise ValueError("Active bookings can only be completed")

        booking.status = new_status
        await self.db.commit()
        await self.db.refresh(booking)
        return BookingRead.model_validate(booking)

