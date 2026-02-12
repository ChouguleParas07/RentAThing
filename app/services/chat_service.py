from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead


class ChatService:
    """Business logic for chat history and message persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.messages = MessageRepository(db)

    async def send_message(
        self,
        *,
        sender_id: UUID,
        payload: MessageCreate,
    ) -> MessageRead:
        if sender_id == payload.receiver_id:
            raise ValueError("Cannot send messages to yourself")

        msg = await self.messages.create(
            sender_id=sender_id,
            receiver_id=payload.receiver_id,
            content=payload.content,
            conversation_id=payload.conversation_id,
        )
        await self.db.commit()
        await self.db.refresh(msg)
        return MessageRead.model_validate(msg)

    async def get_conversation(
        self,
        *,
        user_id: UUID,
        other_user_id: UUID | None,
        conversation_id: str | None,
        skip: int,
        limit: int,
    ) -> MessageListResponse:
        total, messages = await self.messages.list_conversation(
            user_id=user_id,
            other_user_id=other_user_id,
            conversation_id=conversation_id,
            skip=skip,
            limit=limit,
        )
        return MessageListResponse(
            total=total,
            messages=[MessageRead.model_validate(m) for m in messages],
        )

