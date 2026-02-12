from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BookingStatus


class Booking(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.REQUESTED, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    renter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item = relationship("Item", back_populates="bookings", lazy="selectin")
    renter = relationship("User", back_populates="bookings_as_renter", foreign_keys=[renter_id], lazy="selectin")
    owner = relationship("User", back_populates="bookings_as_owner", foreign_keys=[owner_id], lazy="selectin")
    reviews = relationship("Review", back_populates="booking", lazy="selectin")
    escrow_record = relationship("EscrowRecord", back_populates="booking", uselist=False, lazy="selectin")

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_bookings_end_after_start"),
        CheckConstraint("total_price >= 0", name="ck_bookings_total_price_non_negative"),
        Index("ix_bookings_item_id", "item_id"),
        Index("ix_bookings_renter_id", "renter_id"),
        Index("ix_bookings_owner_id", "owner_id"),
        Index("ix_bookings_status", "status"),
    )

