from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageCreate(BaseModel):
    receiver_id: UUID
    content: str
    conversation_id: str | None = None


class MessageRead(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    conversation_id: str | None
    content: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    total: int
    messages: list[MessageRead]

