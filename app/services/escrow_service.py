from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EscrowStatus, UserRole
from app.repositories.booking_repository import BookingRepository
from app.repositories.escrow_repository import EscrowRepository
from app.schemas.escrow import EscrowRead


class EscrowService:
    """Business logic for simulated escrow around bookings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.bookings = BookingRepository(db)
        self.escrows = EscrowRepository(db)

    async def create_and_hold_for_booking(
        self,
        *,
        booking_id: UUID,
        renter_id: UUID,
        owner_id: UUID,
        item_id: UUID,
        amount_held: Decimal,
    ) -> EscrowRead:
        escrow = await self.escrows.create_for_booking(
            booking_id=booking_id,
            renter_id=renter_id,
            owner_id=owner_id,
            item_id=item_id,
            amount_held=amount_held,
        )
        escrow = await self.escrows.mark_held(escrow)
        await self.db.commit()
        return EscrowRead.model_validate(escrow)

    async def get_for_booking(self, booking_id: UUID) -> EscrowRead:
        escrow = await self.escrows.get_by_booking_id(booking_id)
        if not escrow:
            raise LookupError("Escrow record not found")
        return EscrowRead.model_validate(escrow)

    async def cancel_for_booking(self, booking_id: UUID) -> EscrowRead:
        escrow = await self.escrows.get_by_booking_id(booking_id)
        if not escrow:
            raise LookupError("Escrow record not found")
        escrow = await self.escrows.cancel(escrow)
        await self.db.commit()
        return EscrowRead.model_validate(escrow)

    async def settle_for_booking(
        self,
        *,
        booking_id: UUID,
        actor_id: UUID,
        role: UserRole,
        damage_fee: Decimal,
    ) -> EscrowRead:
        booking = await self.bookings.get_by_id(booking_id)
        if not booking:
            raise LookupError("Booking not found")

        if role not in (UserRole.OWNER, UserRole.ADMIN) or actor_id != booking.owner_id:
            raise PermissionError("Only the owner or admin can settle escrow")

        escrow = await self.escrows.get_by_booking_id(booking_id)
        if not escrow:
            raise LookupError("Escrow record not found")

        if escrow.status not in (EscrowStatus.PENDING, EscrowStatus.HELD):
            raise ValueError("Escrow already finalized")

        if damage_fee < 0 or damage_fee > escrow.amount_held:
            raise ValueError("Invalid damage fee")

        escrow = await self.escrows.settle(escrow, damage_fee)
        await self.db.commit()
        return EscrowRead.model_validate(escrow)

