from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        sender_id: UUID,
        receiver_id: UUID,
        content: str,
        conversation_id: str | None,
    ) -> Message:
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            conversation_id=conversation_id,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_conversation(
        self,
        *,
        user_id: UUID,
        other_user_id: UUID | None = None,
        conversation_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, Sequence[Message]]:
        conditions = [
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == user_id),
            )
            if other_user_id
            else or_(Message.sender_id == user_id, Message.receiver_id == user_id)
        ]
        if conversation_id:
            conditions.append(Message.conversation_id == conversation_id)

        base: Select[tuple[Message]] = select(Message).where(and_(*conditions))
        count_stmt = select(func.count()).select_from(base.subquery())
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar_one() or 0)

        stmt = base.order_by(Message.created_at.asc()).offset(skip).limit(limit)
        res = await self.session.execute(stmt)
        return total, res.scalars().all()

