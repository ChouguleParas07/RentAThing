from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    # For future: map chat threads/conversations explicitly
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender = relationship("User", back_populates="messages_sent", foreign_keys=[sender_id], lazy="selectin")
    receiver = relationship("User", back_populates="messages_received", foreign_keys=[receiver_id], lazy="selectin")

    __table_args__ = (
        Index("ix_messages_sender_receiver", "sender_id", "receiver_id"),
    )

