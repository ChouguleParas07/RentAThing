from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int
    iat: int
    jti: str
    roles: list[UserRole] | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class VerifyEmailResponse(BaseModel):
    message: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthenticatedUser(BaseModel):
    id: UUID
    email: EmailStr
    phone: str
    city: str
    full_name: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
