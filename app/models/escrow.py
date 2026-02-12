from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import EscrowStatus


class EscrowRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "escrow_records"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
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
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount_held: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_released: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    damage_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    status: Mapped[EscrowStatus] = mapped_column(default=EscrowStatus.PENDING, nullable=False)

    booking = relationship("Booking", back_populates="escrow_record", lazy="selectin")

    __table_args__ = (
        CheckConstraint("amount_held >= 0", name="ck_escrow_amount_held_non_negative"),
        CheckConstraint("amount_released >= 0", name="ck_escrow_amount_released_non_negative"),
        CheckConstraint("damage_fee >= 0", name="ck_escrow_damage_fee_non_negative"),
        CheckConstraint(
            "amount_released + damage_fee <= amount_held",
            name="ck_escrow_released_plus_damage_lte_held",
        ),
        Index("ix_escrow_booking_id", "booking_id"),
    )

