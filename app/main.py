from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings
from app.api.routes import auth as auth_routes
from app.api.routes import items as items_routes
from app.api.routes import bookings as bookings_routes
from app.api.routes import escrow as escrow_routes
from app.api.routes import reviews as reviews_routes
from app.api.routes import chat as chat_routes


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

    # Routers
    app.include_router(auth_routes.router)
    app.include_router(items_routes.router)
    app.include_router(bookings_routes.router)
    app.include_router(escrow_routes.router)
    app.include_router(reviews_routes.router)
    app.include_router(chat_routes.router)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

