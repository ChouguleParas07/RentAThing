from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, decode_token
from app.db.redis import get_redis
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthenticatedUser, TokenPayload
from app.services.token_blacklist_service import is_token_blacklisted


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def _get_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> TokenPayload:
    try:
        raw_payload = decode_token(token)
        payload = TokenPayload.model_validate(raw_payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    if payload.type != TokenType.ACCESS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    if await is_token_blacklisted(redis, payload.jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    return payload


async def get_current_user(
    payload: Annotated[TokenPayload, Depends(_get_token_payload)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthenticatedUser:
    repo = UserRepository(db)
    user = await repo.get_by_id(payload.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return AuthenticatedUser.model_validate(user)


async def get_current_active_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_roles(*roles: UserRole):
    async def _role_checker(
        user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    ) -> AuthenticatedUser:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _role_checker

