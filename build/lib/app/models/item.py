from __future__ import annotations

from datetime import date
import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Item(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "items"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    daily_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    security_deposit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    location_lat: Mapped[float] = mapped_column(nullable=False)
    location_lng: Mapped[float] = mapped_column(nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    available_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    images: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # store image metadata/URLs

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    owner = relationship("User", back_populates="items", lazy="selectin")
    category = relationship("Category", back_populates="items", lazy="selectin")
    bookings = relationship("Booking", back_populates="item", lazy="selectin")
    reviews = relationship("Review", back_populates="item", lazy="selectin")

    __table_args__ = (
        CheckConstraint("daily_price >= 0", name="ck_items_daily_price_non_negative"),
        CheckConstraint("security_deposit >= 0", name="ck_items_security_deposit_non_negative"),
        Index("ix_items_owner_id", "owner_id"),
        Index("ix_items_category_id", "category_id"),
    )

