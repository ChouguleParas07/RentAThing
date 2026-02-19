"""Structured logging configuration using structlog.

Production: JSON to stdout for log aggregators (e.g. CloudWatch, Datadog).
Local/dev: Colored console with timestamps and key-value pairs.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import get_settings


def _add_app_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add app name and env to every log line."""
    event_dict.setdefault("app", "rent-a-thing")
    event_dict.setdefault("env", get_settings().app_env)
    return event_dict


def configure_logging() -> None:
    """Configure structlog and standard library logging. Call once at startup."""
    settings = get_settings()

    # Shared processors for all outputs
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        _add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.app_env == "prod":
        # JSON for production (machine-readable)
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Colored console for local/dev
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.app_debug else logging.INFO,
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING if settings.app_env == "prod" else logging.INFO
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound logger for the given module name."""
    return structlog.get_logger(name)
