"""Health check helpers for liveness and readiness."""

from __future__ import annotations

from sqlalchemy import text

from app.db.redis import redis_client
from app.db.session import engine


async def check_readiness() -> dict:
    """Check DB and Redis connectivity. Used by /health/ready."""
    db_ok = False
    redis_ok = False

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        await redis_client.ping()
        redis_ok = True
    except Exception:
        pass

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
