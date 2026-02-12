from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.escrow import EscrowRecord
from app.models.enums import EscrowStatus


class EscrowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_booking_id(self, booking_id: UUID) -> EscrowRecord | None:
        stmt = select(EscrowRecord).where(EscrowRecord.booking_id == booking_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_for_booking(
        self,
        *,
        booking_id: UUID,
        renter_id: UUID,
        owner_id: UUID,
        item_id: UUID,
        amount_held: Decimal,
    ) -> EscrowRecord:
        escrow = EscrowRecord(
            booking_id=booking_id,
            renter_id=renter_id,
            owner_id=owner_id,
            item_id=item_id,
            amount_held=amount_held,
            status=EscrowStatus.PENDING,
        )
        self.session.add(escrow)
        await self.session.flush()
        await self.session.refresh(escrow)
        return escrow

    async def mark_held(self, escrow: EscrowRecord) -> EscrowRecord:
        escrow.status = EscrowStatus.HELD
        await self.session.flush()
        await self.session.refresh(escrow)
        return escrow

    async def cancel(self, escrow: EscrowRecord) -> EscrowRecord:
        escrow.status = EscrowStatus.CANCELLED
        escrow.amount_released = escrow.amount_held
        await self.session.flush()
        await self.session.refresh(escrow)
        return escrow

    async def settle(self, escrow: EscrowRecord, damage_fee: Decimal) -> EscrowRecord:
        escrow.damage_fee = damage_fee
        escrow.amount_released = escrow.amount_held - damage_fee
        escrow.status = EscrowStatus.RELEASED
        await self.session.flush()
        await self.session.refresh(escrow)
        return escrow

