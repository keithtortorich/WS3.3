"""Shared pytest fixtures: SQLite-backed async engine + FastAPI test client
with the get_db/auth dependencies overridden so integration tests don't need
real Postgres/Clerk services.
"""
from __future__ import annotations

from typing import AsyncGenerator

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.auth import get_current_org, get_current_user, AuthContext
from app.core.db import get_db
from app.main import create_app
from app.models.base import Base

TEST_ORG_ID = uuid.uuid4()
TEST_USER_ID = uuid.uuid4()


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator:
    """In-memory SQLite engine, shared across connections via StaticPool
    (required for SQLite ':memory:' to survive across the async session's
    multiple connections within a single test)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def app(async_engine) -> AsyncGenerator:
    """Build a FastAPI test app with the common dependencies overridden."""
    session_factory = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    async def _override_get_current_user():
        return AuthContext(
            user_id=str(TEST_USER_ID),
            org_id=str(TEST_ORG_ID),
            org_role="org:owner",
            email="test@example.com",
            raw_claims={},
        )

    async def _override_get_current_org():
        return str(TEST_ORG_ID)

    application = create_app()
    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_current_user] = _override_get_current_user
    application.dependency_overrides[get_current_org] = _override_get_current_org

    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client against the FastAPI app returned by ``app``."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
