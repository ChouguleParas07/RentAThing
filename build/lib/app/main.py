from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings


def create_app() -> FastAPI:
    """Application factory for creating a FastAPI instance.

    Keeps app creation testable and configurable.
    """

    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url="/redoc" if settings.app_env != "prod" else None,
        openapi_url="/openapi.json" if settings.app_env != "prod" else None,
    )

    # TODO: include routers here (auth, items, bookings, etc.)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

