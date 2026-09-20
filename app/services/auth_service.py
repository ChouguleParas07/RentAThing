from __future__ import annotations

import secrets
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
from app.schemas.auth import (
    AuthenticatedUser,
    ForgotPasswordResponse,
    RegisterResponse,
    ResetPasswordResponse,
    TokenPair,
    VerifyEmailResponse,
)
from app.schemas.user import UserCreate, UserUpdate
from app.services.token_blacklist_service import blacklist_token, is_token_blacklisted


class AuthService:
    """Business logic for authentication and authorization."""

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.users = UserRepository(db)
        self._verification_ttl_seconds = 10 * 60

    async def register_user(self, data: UserCreate) -> RegisterResponse:
        existing = await self.users.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        existing_phone = await self.users.get_by_phone(data.phone)
        if existing_phone:
            raise ValueError("Phone number already registered")

        hashed_password = get_password_hash(data.password)
        user = await self.users.create_user(
            email=data.email,
            phone=data.phone,
            city=data.city,
            hashed_password=hashed_password,
            full_name=data.full_name,
            role=data.role,
        )
        await self.db.commit()
        await self.db.refresh(user)

        # Simulate email verification code generation.
        verification_code = str(secrets.randbelow(900000) + 100000)
        await self.redis.set(
            f"email_verification:{data.email.lower()}",
            verification_code,
            ex=self._verification_ttl_seconds,
        )

        return RegisterResponse(
            message="Registration successful. Verify your email using the code."
        )

    async def verify_email(self, email: str, code: str) -> VerifyEmailResponse:
        key = f"email_verification:{email.lower()}"
        stored_code = await self.redis.get(key)
        if not stored_code:
            raise ValueError("Verification code expired or not found")
        if stored_code != code:
            raise ValueError("Invalid verification code")

        user = await self.users.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        user.is_verified = True
        await self.db.commit()
        await self.redis.delete(key)

        return VerifyEmailResponse(message="Email verified successfully")

    async def authenticate_user(self, email: str, password: str) -> tuple[AuthenticatedUser, TokenPair]:
        user = await self.users.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise PermissionError("User is inactive")
        if not user.is_verified:
            raise PermissionError("Email not verified")

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
        
        # Blacklist the old refresh token to prevent replay attacks
        if isinstance(payload.get("exp"), int):
            await blacklist_token(self.redis, jti, payload.get("exp"))
            
        return TokenPair(access_token=access, refresh_token=new_refresh)

    async def logout(self, token: str) -> None:
        """Blacklists the given token (access or refresh)."""

        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and isinstance(exp, int):
            await blacklist_token(self.redis, jti, exp)

    async def forgot_password(self, email: str) -> ForgotPasswordResponse:
        user = await self.users.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        verification_code = str(secrets.randbelow(900000) + 100000)
        key = f"password_reset:{email.lower()}"
        await self.redis.set(
            key,
            verification_code,
            ex=self._verification_ttl_seconds,
        )

        return ForgotPasswordResponse(
            message="Password reset code generated."
        )

    async def reset_password(self, email: str, code: str, new_password: str) -> ResetPasswordResponse:
        key = f"password_reset:{email.lower()}"
        stored_code = await self.redis.get(key)
        if not stored_code:
            raise ValueError("Reset code expired or not found")
        if stored_code != code:
            raise ValueError("Invalid reset code")

        user = await self.users.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        await self.db.commit()
        await self.redis.delete(key)

        return ResetPasswordResponse(message="Password reset successful")


    async def update_profile(self, user_id: str, data: UserUpdate) -> AuthenticatedUser:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if data.email is not None and data.email != user.email:
            existing_email = await self.users.get_by_email(data.email)
            if existing_email:
                raise ValueError("Email already in use")
            user.email = data.email
            # Usually we might unverify them if email changes, but simple for now
            user.is_verified = False
            # Generate new code...
            verification_code = str(secrets.randbelow(900000) + 100000)
            await self.redis.set(
                f"email_verification:{data.email.lower()}",
                verification_code,
                ex=self._verification_ttl_seconds,
            )

        if data.phone is not None and data.phone != user.phone:
            existing_phone = await self.users.get_by_phone(data.phone)
            if existing_phone:
                raise ValueError("Phone number already in use")
            user.phone = data.phone

        if data.city is not None:
            user.city = data.city

        if data.full_name is not None:
            user.full_name = data.full_name

        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url

        if data.password is not None:
            user.hashed_password = get_password_hash(data.password)

        await self.db.commit()
        await self.db.refresh(user)
        return AuthenticatedUser.model_validate(user)

