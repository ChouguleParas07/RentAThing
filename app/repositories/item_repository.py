from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item


class ItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, item_id: UUID) -> Item | None:
        stmt = select(Item).where(Item.id == item_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_items(
        self,
        *,
        owner_id: UUID | None = None,
        category_id: UUID | None = None,
        is_active: bool | None = True,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[int, Sequence[Item]]:
        conditions = []
        if owner_id is not None:
            conditions.append(Item.owner_id == owner_id)
        if category_id is not None:
            conditions.append(Item.category_id == category_id)
        if is_active is not None:
            conditions.append(Item.is_active == is_active)

        base_stmt: Select[tuple[Item]] = select(Item)
        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))

        # Count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar_one() or 0)

        # Page
        stmt = base_stmt.order_by(Item.created_at.desc()).offset(skip).limit(limit)
        res = await self.session.execute(stmt)
        items = res.scalars().all()
        return total, items

    async def create_item(
        self,
        *,
        owner_id: UUID,
        title: str,
        description: str | None,
        daily_price,
        security_deposit,
        location_lat: float,
        location_lng: float,
        location_text: str | None,
        available_from,
        available_until,
        category_id: UUID | None,
    ) -> Item:
        item = Item(
            owner_id=owner_id,
            title=title,
            description=description,
            daily_price=daily_price,
            security_deposit=security_deposit,
            location_lat=location_lat,
            location_lng=location_lng,
            location_text=location_text,
            available_from=available_from,
            available_until=available_until,
            category_id=category_id,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete(self, item: Item) -> None:
        await self.session.delete(item)

