from __future__ import annotations

from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    """Data access layer for users."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str | None,
        role: UserRole,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_last_login(self, user: User) -> None:
        from datetime import datetime, timezone

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def list_by_ids(self, ids: Iterable[UUID]) -> list[User]:
        stmt = select(User).where(User.id.in_(list(ids)))
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

