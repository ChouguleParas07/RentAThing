from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import BookingStatus, UserRole
from app.models.item import Item
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewRead


class ReviewService:
    """Business logic for reviews and trust scores."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.reviews = ReviewRepository(db)

    async def _ensure_booking_reviewable(
        self,
        *,
        booking_id: UUID,
        author_id: UUID,
        item_id: UUID,
        target_user_id: UUID,
    ) -> Booking:
        booking = await self.db.get(Booking, booking_id)
        if not booking:
            raise LookupError("Booking not found")
        if booking.status != BookingStatus.COMPLETED:
            raise ValueError("Only completed bookings can be reviewed")
        if booking.item_id != item_id:
            raise ValueError("Booking not for given item")
        if author_id not in (booking.renter_id, booking.owner_id):
            raise PermissionError("You are not part of this booking")
        if target_user_id not in (booking.renter_id, booking.owner_id):
            raise ValueError("Target user is not part of this booking")
        if target_user_id == author_id:
            raise ValueError("Cannot review yourself")
        return booking

    async def _recalculate_item_rating(self, item_id: UUID) -> None:
        stmt = (
            select(func.avg(Item.reviews.property.mapper.class_.rating), func.count(Item.reviews.property.mapper.class_.id))
            .select_from(Item)
            .join(Item.reviews)
            .where(Item.id == item_id)
        )
        res = await self.db.execute(stmt)
        avg_rating, count = res.first() or (None, 0)
        item = await self.db.get(Item, item_id)
        if item:
            item.avg_rating = float(avg_rating) if avg_rating is not None else None
            item.rating_count = int(count or 0)
            await self.db.flush()

    async def _recalculate_user_trust(self, user_id: UUID) -> None:
        stmt = (
            select(func.avg(User.reviews_received.property.mapper.class_.rating), func.count(User.reviews_received.property.mapper.class_.id))
            .select_from(User)
            .join(User.reviews_received)
            .where(User.id == user_id)
        )
        res = await self.db.execute(stmt)
        avg_rating, count = res.first() or (None, 0)
        user = await self.db.get(User, user_id)
        if user:
            user.avg_rating = float(avg_rating) if avg_rating is not None else None
            user.rating_count = int(count or 0)
            # Simple trust score heuristic: base on rating and volume
            if user.avg_rating is not None:
                volume_factor = min(user.rating_count / 10, 1)  # up to 10 reviews to reach full weight
                user.trust_score = round(user.avg_rating * 20 * volume_factor, 2)  # 0–100
            await self.db.flush()

    async def create_review(
        self,
        *,
        author_id: UUID,
        author_role: UserRole,
        payload: ReviewCreate,
    ) -> ReviewRead:
        await self._ensure_booking_reviewable(
            booking_id=payload.booking_id,
            author_id=author_id,
            item_id=payload.item_id,
            target_user_id=payload.target_user_id,
        )

        review = await self.reviews.create(
            rating=payload.rating,
            comment=payload.comment,
            item_id=payload.item_id,
            booking_id=payload.booking_id,
            author_id=author_id,
            target_user_id=payload.target_user_id,
        )

        # Recalculate aggregates
        await self._recalculate_item_rating(payload.item_id)
        await self._recalculate_user_trust(payload.target_user_id)

        await self.db.commit()
        await self.db.refresh(review)
        return ReviewRead.model_validate(review)

    async def list_item_reviews(self, item_id: UUID, skip: int, limit: int) -> ReviewListResponse:
        total, reviews = await self.reviews.list_for_item(item_id=item_id, skip=skip, limit=limit)
        return ReviewListResponse(
            total=total,
            reviews=[ReviewRead.model_validate(r) for r in reviews],
        )

    async def list_user_reviews(self, user_id: UUID, skip: int, limit: int) -> ReviewListResponse:
        total, reviews = await self.reviews.list_for_user(user_id=user_id, skip=skip, limit=limit)
        return ReviewListResponse(
            total=total,
            reviews=[ReviewRead.model_validate(r) for r in reviews],
        )

