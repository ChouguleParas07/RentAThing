from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.RENTER, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships (back_populates defined in related models)
    items = relationship("Item", back_populates="owner", lazy="selectin")
    bookings_as_renter = relationship("Booking", back_populates="renter", foreign_keys="Booking.renter_id", lazy="selectin")
    bookings_as_owner = relationship("Booking", back_populates="owner", foreign_keys="Booking.owner_id", lazy="selectin")
    reviews_written = relationship("Review", back_populates="author", foreign_keys="Review.author_id", lazy="selectin")
    reviews_received = relationship("Review", back_populates="target_user", foreign_keys="Review.target_user_id", lazy="selectin")
    messages_sent = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id", lazy="selectin")
    messages_received = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id", lazy="selectin")

    __table_args__ = (
        Index("ix_users_email_role", "email", "role"),
    )

