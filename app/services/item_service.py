from __future__ import annotations

from uuid import UUID
import json

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.item import Item
from app.repositories.category_repository import CategoryRepository
from app.repositories.item_repository import ItemRepository
from app.schemas.item import ItemCreate, ItemListResponse, ItemRead, ItemUpdate


class ItemService:
    """Business logic for item management."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None) -> None:
        self.db = db
        self.redis = redis
        self.items = ItemRepository(db)
        self.categories = CategoryRepository(db)
        self._cache_ttl_seconds = 60

    async def create_item(self, owner_id: UUID, payload: ItemCreate) -> ItemRead:
        if payload.category_id:
            category = await self.categories.get_by_id(payload.category_id)
            if not category:
                raise ValueError("Category not found")

        item = await self.items.create_item(
            owner_id=owner_id,
            title=payload.title,
            description=payload.description,
            daily_price=payload.daily_price,
            security_deposit=payload.security_deposit,
            location_lat=payload.location_lat,
            location_lng=payload.location_lng,
            location_text=payload.location_text,
            available_from=payload.available_from,
            available_until=payload.available_until,
            category_id=payload.category_id,
        )
        await self.db.commit()
        await self.db.refresh(item)
        return ItemRead.model_validate(item)

    async def list_items(
        self,
        *,
        owner_id: UUID | None,
        category_id: UUID | None,
        is_active: bool | None,
        skip: int,
        limit: int,
    ) -> ItemListResponse:
        # Try cache if Redis is available
        cache_key = None
        if self.redis is not None:
            cache_key = (
                f"items:list:owner={owner_id}|cat={category_id}|active={is_active}|"
                f"skip={skip}|limit={limit}"
            )
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return ItemListResponse.model_validate(data)

        total, items = await self.items.list_items(
            owner_id=owner_id,
            category_id=category_id,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )
        response = ItemListResponse(
            total=total,
            items=[ItemRead.model_validate(item) for item in items],
        )
        if self.redis is not None and cache_key is not None:
            await self.redis.set(cache_key, response.model_dump_json(), ex=self._cache_ttl_seconds)
        return response

    async def get_item(self, item_id: UUID) -> ItemRead:
        item = await self.items.get_by_id(item_id)
        if not item:
            raise LookupError("Item not found")
        return ItemRead.model_validate(item)

    async def _ensure_owner_or_admin(self, current_user_id: UUID, role: UserRole, item: Item) -> None:
        if role == UserRole.ADMIN:
            return
        if item.owner_id != current_user_id:
            raise PermissionError("You do not own this item")

    async def update_item(
        self,
        *,
        item_id: UUID,
        current_user_id: UUID,
        role: UserRole,
        payload: ItemUpdate,
    ) -> ItemRead:
        item = await self.items.get_by_id(item_id)
        if not item:
            raise LookupError("Item not found")

        await self._ensure_owner_or_admin(current_user_id, role, item)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        await self.db.commit()
        await self.db.refresh(item)
        # Invalidate item list cache
        if self.redis is not None:
            async for key in self.redis.scan_iter("items:list:*"):
                await self.redis.delete(key)
        return ItemRead.model_validate(item)

    async def delete_item(
        self,
        *,
        item_id: UUID,
        current_user_id: UUID,
        role: UserRole,
    ) -> None:
        item = await self.items.get_by_id(item_id)
        if not item:
            raise LookupError("Item not found")

        await self._ensure_owner_or_admin(current_user_id, role, item)
        await self.items.delete(item)
        await self.db.commit()
        # Invalidate item list cache
        if self.redis is not None:
            async for key in self.redis.scan_iter("items:list:*"):
                await self.redis.delete(key)

