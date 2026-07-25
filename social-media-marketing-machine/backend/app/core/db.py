"""Async SQLAlchemy engine/session setup + FastAPI dependency.

A module-level engine/sessionmaker pair is created lazily so that tests can
override ``DATABASE_URL`` (via ``TEST_DATABASE_URL`` / dependency override)
without importing a real Postgres engine at all.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# `future=True` / 2.0-style engine. `pool_pre_ping` avoids serving stale
# connections after a DB restart, which matters for long-lived worker/API
# processes talking to a containerized Postgres.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped AsyncSession.

    Wrapped in a try/finally (not a context manager decorator) so that a
    caught exception still closes the session before propagating.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
