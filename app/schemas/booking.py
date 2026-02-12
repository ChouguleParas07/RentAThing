from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import BookingStatus


class BookingBase(BaseModel):
    start_date: date
    end_date: date
    notes: str | None = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:  # type: ignore[override]
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v


class BookingCreate(BookingBase):
    item_id: UUID


class BookingRead(BaseModel):
    id: UUID
    item_id: UUID
    renter_id: UUID
    owner_id: UUID
    start_date: date
    end_date: date
    total_price: Decimal
    status: BookingStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookingListResponse(BaseModel):
    total: int
    bookings: list[BookingRead]


class BookingStatusUpdate(BaseModel):
    status: BookingStatus

