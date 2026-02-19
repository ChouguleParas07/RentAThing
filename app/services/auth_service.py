from __future__ import annotations

from typing import Iterable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthenticatedUser, TokenPair
from app.schemas.user import UserCreate
from app.services.token_blacklist_service import blacklist_token, is_token_blacklisted


class AuthService:
    """Business logic for authentication and authorization."""

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.users = UserRepository(db)

    async def register_user(self, data: UserCreate):
        existing = await self.users.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        hashed_password = get_password_hash(data.password)
        user = await self.users.create_user(
            email=data.email,
            hashed_password=hashed_password,
            full_name=data.full_name,
            role=data.role,
        )
        await self.db.commit()
        await self.db.refresh(user)
        # Return the ORM user object so callers can produce the appropriate
        # response model (e.g. `UserRead` which expects timestamps).
        return user

    async def authenticate_user(self, email: str, password: str) -> tuple[AuthenticatedUser, TokenPair]:
        user = await self.users.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise PermissionError("User is inactive")

        await self.users.update_last_login(user)
        await self.db.commit()

        roles: Iterable[UserRole] = [user.role]
        access = create_access_token(subject=str(user.id), roles=roles)
        refresh = create_refresh_token(subject=str(user.id), roles=roles)
        return AuthenticatedUser.model_validate(user), TokenPair(access_token=access, refresh_token=refresh)

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token)
        if payload.get("type") != TokenType.REFRESH:
            raise ValueError("Invalid refresh token")

        jti = payload.get("jti")
        if not jti or await is_token_blacklisted(self.redis, jti):
            raise PermissionError("Token revoked")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")

        user = await self.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise PermissionError("User not found or inactive")

        roles: Iterable[UserRole] = [user.role]
        access = create_access_token(subject=str(user.id), roles=roles)
        new_refresh = create_refresh_token(subject=str(user.id), roles=roles)
        return TokenPair(access_token=access, refresh_token=new_refresh)

    async def logout(self, token: str) -> None:
        """Blacklists the given token (access or refresh)."""

        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and isinstance(exp, int):
            await blacklist_token(self.redis, jti, exp)

