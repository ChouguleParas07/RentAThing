from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.models.enums import UserRole


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    roles: Iterable[UserRole] | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())

    to_encode: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": jti,
    }
    if roles is not None:
        to_encode["roles"] = [role.value for role in roles]
    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_access_token(
    *,
    subject: str,
    roles: Iterable[UserRole] | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        expires_delta=expires_delta,
        roles=roles,
        additional_claims=additional_claims,
    )


def create_refresh_token(
    *,
    subject: str,
    roles: Iterable[UserRole] | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    return _create_token(
        subject=subject,
        token_type=TokenType.REFRESH,
        expires_delta=expires_delta,
        roles=roles,
        additional_claims=additional_claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

