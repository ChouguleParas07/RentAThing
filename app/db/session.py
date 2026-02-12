from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


settings = get_settings()


def get_engine() -> AsyncEngine:
    """Create the global async SQLAlchemy engine.

    The engine should typically be created once per process.
    """

    return create_async_engine(
        settings.database_url,
        echo=settings.app_debug,
        pool_pre_ping=True,
    )


engine: AsyncEngine = get_engine()

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that provides an async DB session.

    Ensures the session is properly closed after each request.
    """

    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()

