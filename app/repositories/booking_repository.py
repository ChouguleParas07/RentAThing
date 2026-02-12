from __future__ import annotations

from datetime import date
from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import BookingStatus


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        stmt = select(Booking).where(Booking.id == booking_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_for_renter(
        self,
        renter_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[int, Sequence[Booking]]:
        base: Select[tuple[Booking]] = select(Booking).where(Booking.renter_id == renter_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar_one() or 0)

        stmt = base.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        res = await self.session.execute(stmt)
        return total, res.scalars().all()

    async def list_for_owner(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[int, Sequence[Booking]]:
        base: Select[tuple[Booking]] = select(Booking).where(Booking.owner_id == owner_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar_one() or 0)

        stmt = base.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        res = await self.session.execute(stmt)
        return total, res.scalars().all()

    async def has_overlapping_booking(
        self,
        *,
        item_id: UUID,
        start_date: date,
        end_date: date,
    ) -> bool:
        """Return True if there is any non-cancelled/non-completed booking overlapping the given range."""

        active_statuses: list[BookingStatus] = [
            BookingStatus.REQUESTED,
            BookingStatus.APPROVED,
            BookingStatus.ACTIVE,
        ]
        stmt = select(func.count()).select_from(Booking).where(
            and_(
                Booking.item_id == item_id,
                Booking.status.in_(active_statuses),
                # overlapping ranges: (start <= existing_end) and (end >= existing_start)
                Booking.start_date <= end_date,
                Booking.end_date >= start_date,
            )
        )
        res = await self.session.execute(stmt)
        count = int(res.scalar_one() or 0)
        return count > 0

    async def create(
        self,
        *,
        item_id: UUID,
        renter_id: UUID,
        owner_id: UUID,
        start_date: date,
        end_date: date,
        total_price,
        notes: str | None,
    ) -> Booking:
        booking = Booking(
            item_id=item_id,
            renter_id=renter_id,
            owner_id=owner_id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            notes=notes,
        )
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)
        return booking

