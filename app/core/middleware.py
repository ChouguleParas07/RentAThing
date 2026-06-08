"""HTTP middleware: request logging, request ID propagation."""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import structlog.contextvars

from app.core.exceptions import error_response
from app.core.logging_config import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request: method, path, status, duration. Propagate X-Request-ID."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id  # for exception handlers
        start = time.perf_counter()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                query=str(request.query_params) or None,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                client_host=request.client.host if request.client else None,
            )
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        except BaseExceptionGroup as exc:
            logger.exception(
                "unhandled_exception_group",
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
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()


# Security headers applied to all responses (production best practice)
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value
        return response
