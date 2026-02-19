from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.health import check_readiness
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
    configure_logging()

    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url="/redoc" if settings.app_env != "prod" else None,
        openapi_url="/openapi.json" if settings.app_env != "prod" else None,
    )

    # Exception handlers (consistent JSON and logging)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Middleware (last added = outermost): security headers, CORS, then request logging
    app.add_middleware(RequestLoggingMiddleware)
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    # Routers
    app.include_router(auth_routes.router)
    app.include_router(items_routes.router)
    app.include_router(bookings_routes.router)
    app.include_router(escrow_routes.router)
    app.include_router(reviews_routes.router)
    app.include_router(chat_routes.router)

    @app.get("/health", tags=["health"])
    async def health_liveness() -> dict[str, str]:
        """Liveness: is the process up? No dependencies."""
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"], response_model=None)
    async def health_readiness() -> dict | JSONResponse:
        """Readiness: can we serve traffic? Checks DB and Redis."""
        result = await check_readiness()
        if result["status"] != "ok":
            return JSONResponse(status_code=503, content=result)
        return result

    # Simple frontend: serve from /app so API and UI are same origin
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.is_dir():
        @app.get("/app", tags=["frontend"])
        @app.get("/app/", tags=["frontend"])
        async def serve_frontend() -> FileResponse:
            index = frontend_dir / "index.html"
            if not index.is_file():
                raise StarletteHTTPException(404)
            return FileResponse(index)

        app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()

