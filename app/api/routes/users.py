from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.schemas.auth import AuthenticatedUser
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=dict)
async def list_users(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    repo = UserRepository(db)
    total, items = await repo.list(skip=skip, limit=limit)
    
    # Using AuthenticatedUser as the schema to return for the list items,
    # because it already omits hashed_password.
    return {
        "items": [AuthenticatedUser.model_validate(u) for u in items],
        "total": total
    }
