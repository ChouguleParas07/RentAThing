from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, review_id: UUID) -> Review | None:
        stmt = select(Review).where(Review.id == review_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_for_item(self, item_id: UUID, skip: int, limit: int) -> tuple[int, Sequence[Review]]:
        base: Select[tuple[Review]] = select(Review).where(Review.item_id == item_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar_one() or 0)

        stmt = base.order_by(Review.created_at.desc()).offset(skip).limit(limit)
        res = await self.session.execute(stmt)
        return total, res.scalars().all()

    async def list_for_user(self, user_id: UUID, skip: int, limit: int) -> tuple[int, Sequence[Review]]:
        base: Select[tuple[Review]] = select(Review).where(Review.target_user_id == user_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar_one() or 0)

        stmt = base.order_by(Review.created_at.desc()).offset(skip).limit(limit)
        res = await self.session.execute(stmt)
        return total, res.scalars().all()

    async def create(
        self,
        *,
        rating: int,
        comment: str | None,
        item_id: UUID,
        booking_id: UUID,
        author_id: UUID,
        target_user_id: UUID,
    ) -> Review:
        review = Review(
            rating=rating,
            comment=comment,
            item_id=item_id,
            booking_id=booking_id,
            author_id=author_id,
            target_user_id=target_user_id,
        )
        self.session.add(review)
        await self.session.flush()
        await self.session.refresh(review)
        return review

