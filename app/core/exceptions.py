"""Centralized exception handling and error response format."""

from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging_config import get_logger

logger = get_logger(__name__)


def error_response(
    status_code: int,
    detail: str | list[dict[str, Any]],
    request_id: str | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    """Standard error body for API responses."""
    body: dict[str, Any] = {"detail": detail}
    if request_id:
        body["request_id"] = request_id
    if error_code:
        body["error_code"] = error_code
    return body


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle FastAPI/Starlette HTTPException → consistent JSON and logging."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    status_code = exc.status_code
    detail = exc.detail

    if status_code >= 500:
        logger.exception("http_error", status_code=status_code, detail=detail, path=request.url.path)
    else:
        logger.warning("http_error", status_code=status_code, detail=detail, path=request.url.path)

    response = JSONResponse(
        status_code=status_code,
        content=error_response(status_code, detail, request_id=request_id),
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors (422) with structured detail."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    errors = exc.errors()
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=errors,
    )
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors,
            request_id=request_id,
            error_code="VALIDATION_ERROR",
        ),
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all for unhandled exceptions; log full traceback, return 500."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        exc_info=exc,
    )
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
            request_id=request_id,
            error_code="INTERNAL_ERROR",
        ),
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response
