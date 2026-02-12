from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.db.session import get_db_session
from app.schemas.auth import AuthenticatedUser
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewRead
from app.services.review_service import ReviewService


router = APIRouter(prefix="/reviews", tags=["reviews"])


def get_review_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> ReviewService:
    return ReviewService(db)


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> ReviewRead:
    try:
        return await service.create_review(
            author_id=current_user.id,
            author_role=current_user.role,
            payload=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/items/{item_id}", response_model=ReviewListResponse)
async def list_item_reviews(
    item_id: UUID,
    service: Annotated[ReviewService, Depends(get_review_service)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> ReviewListResponse:
    return await service.list_item_reviews(item_id=item_id, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=ReviewListResponse)
async def list_user_reviews(
    user_id: UUID,
    service: Annotated[ReviewService, Depends(get_review_service)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> ReviewListResponse:
    return await service.list_user_reviews(user_id=user_id, skip=skip, limit=limit)

