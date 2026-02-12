from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, category_id: UUID) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_all(self) -> Sequence[Category]:
        stmt = select(Category).order_by(Category.name)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def create(self, name: str, slug: str, description: str | None) -> Category:
        category = Category(name=name, slug=slug, description=description)
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

