from __future__ import annotations

from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import require_roles
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])

def get_category_repo(db: Annotated[AsyncSession, Depends(get_db_session)]) -> CategoryRepository:
    return CategoryRepository(db)

@router.get("", response_model=list[CategoryRead])
async def list_categories(
    repo: Annotated[CategoryRepository, Depends(get_category_repo)],
) -> Sequence[CategoryRead]:
    categories = await repo.list_all()
    return [CategoryRead.model_validate(c) for c in categories]

@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def create_category(
    payload: CategoryCreate,
    repo: Annotated[CategoryRepository, Depends(get_category_repo)],
) -> CategoryRead:
    existing = await repo.get_by_slug(payload.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this slug already exists")
    category = await repo.create(name=payload.name, slug=payload.slug, description=payload.description)
    return CategoryRead.model_validate(category)

@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    repo: Annotated[CategoryRepository, Depends(get_category_repo)],
) -> CategoryRead:
    category = await repo.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if payload.name is not None:
        category.name = payload.name
    if payload.slug is not None:
        existing = await repo.get_by_slug(payload.slug)
        if existing and existing.id != category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")
        category.slug = payload.slug
    if payload.description is not None:
        category.description = payload.description
    
    await repo.session.commit()
    await repo.session.refresh(category)
    return CategoryRead.model_validate(category)

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def delete_category(
    category_id: UUID,
    repo: Annotated[CategoryRepository, Depends(get_category_repo)],
) -> None:
    category = await repo.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await repo.session.delete(category)
    await repo.session.commit()
