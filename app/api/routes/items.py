from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.api.deps.auth import require_roles
from app.db.session import get_db_session
from app.db.redis import get_redis
from app.models.enums import UserRole
from app.schemas.auth import AuthenticatedUser
from app.schemas.item import ItemCreate, ItemListResponse, ItemRead, ItemUpdate
from app.services.item_service import ItemService


router = APIRouter(prefix="/items", tags=["items"])


def get_item_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ItemService:
    return ItemService(db, redis)


@router.post(
    "",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))],
)
async def create_item(
    payload: ItemCreate,
    current_user: Annotated[AuthenticatedUser, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemRead:
    try:
        return await service.create_item(owner_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=ItemListResponse)
async def list_items(
    service: Annotated[ItemService, Depends(get_item_service)],
    owner_id: UUID | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    is_active: bool | None = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> ItemListResponse:
    return await service.list_items(
        owner_id=owner_id,
        category_id=category_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: UUID,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemRead:
    try:
        return await service.get_item(item_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/{item_id}",
    response_model=ItemRead,
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))],
)
async def update_item(
    item_id: UUID,
    payload: ItemUpdate,
    current_user: Annotated[AuthenticatedUser, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemRead:
    try:
        return await service.update_item(
            item_id=item_id,
            current_user_id=current_user.id,
            role=current_user.role,
            payload=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))],
)
async def delete_item(
    item_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> None:
    try:
        await service.delete_item(
            item_id=item_id,
            current_user_id=current_user.id,
            role=current_user.role,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

