from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewCreate(ReviewBase):
    booking_id: UUID
    item_id: UUID
    target_user_id: UUID


class ReviewRead(BaseModel):
    id: UUID
    rating: int
    comment: str | None
    item_id: UUID
    booking_id: UUID
    author_id: UUID
    target_user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    total: int
    reviews: list[ReviewRead]

