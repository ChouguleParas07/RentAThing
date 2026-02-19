from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Uses Pydantic v2 BaseSettings for type-safe configuration.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: Literal["local", "dev", "staging", "prod"] = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="Rent-a-Thing API", alias="APP_NAME")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    # Security / Auth
    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Database
    postgres_host: str = Field(default="db", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="rentathing", alias="POSTGRES_USER")
    postgres_password: str = Field(default="rentathing", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="rentathing", alias="POSTGRES_DB")
    database_url: str = Field(
        default="postgresql+asyncpg://rentathing:rentathing@db:5432/rentathing",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: AnyUrl = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # Celery
    celery_broker_url: AnyUrl = Field(default="redis://redis:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: AnyUrl = Field(default="redis://redis:6379/2", alias="CELERY_RESULT_BACKEND")

    # CORS (comma-separated origins, e.g. "https://app.example.com,https://admin.example.com")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    This avoids re-reading the environment on each import and keeps startup fast.
    """

    return Settings()  # type: ignore[call-arg]

