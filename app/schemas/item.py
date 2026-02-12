from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.category import CategoryRead


class ItemBase(BaseModel):
    title: str = Field(max_length=255)
    description: str | None = None
    daily_price: Decimal = Field(gt=0)
    security_deposit: Decimal = Field(ge=0)
    location_lat: float
    location_lng: float
    location_text: str | None = None
    available_from: date | None = None
    available_until: date | None = None
    category_id: UUID | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    daily_price: Decimal | None = Field(default=None)
    security_deposit: Decimal | None = Field(default=None)
    location_lat: float | None = None
    location_lng: float | None = None
    location_text: str | None = None
    available_from: date | None = None
    available_until: date | None = None
    category_id: UUID | None = None
    is_active: bool | None = None


class ItemRead(BaseModel):
    id: UUID
    owner_id: UUID
    category: CategoryRead | None = None
    title: str
    description: str | None
    daily_price: Decimal
    security_deposit: Decimal
    location_lat: float
    location_lng: float
    location_text: str | None
    is_active: bool
    available_from: date | None
    available_until: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItemListResponse(BaseModel):
    total: int
    items: list[ItemRead]

