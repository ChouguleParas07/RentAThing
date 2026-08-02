from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import bearer_scheme, get_current_active_user
from app.api.deps.runtime_limits import rate_limit_login
from app.db.redis import get_redis
from app.db.session import get_db_session
from app.schemas.auth import (
    AuthenticatedUser,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenPair,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> AuthService:
    return AuthService(db=db, redis=redis)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> RegisterResponse:
    try:
        return await auth_service.register_user(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    body: VerifyEmailRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> VerifyEmailResponse:
    try:
        return await auth_service.verify_email(body.email, body.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/login", response_model=TokenPair, dependencies=[Depends(rate_limit_login)])
async def login(
    credentials: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPair:
    try:
        _, tokens = await auth_service.authenticate_user(credentials.email, credentials.password)
        return tokens
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(
    body: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPair:
    try:
        return await auth_service.refresh_tokens(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    # Blacklist the current access token
    await auth_service.logout(credentials.credentials)


@router.get("/me", response_model=AuthenticatedUser)
async def read_current_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
) -> AuthenticatedUser:
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    body: ForgotPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ForgotPasswordResponse:
    try:
        return await auth_service.forgot_password(body.email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    body: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ResetPasswordResponse:
    try:
        return await auth_service.reset_password(body.email, body.code, body.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

