"""Alembic environment configuration.

Supports both PostgreSQL (production/dev, via the sync ``psycopg`` driver —
``DATABASE_URL_SYNC``) and SQLite (for fast local testing / CI, via
``TEST_DATABASE_URL``) so the same migration environment works everywhere.

Dialect-specific limitation: the initial migration (see
``alembic/versions/``) uses PostgreSQL-flavored types (``JSONB``, ``ARRAY``,
native ``Enum``) through the ``JSONBCompat`` / ``StringArrayCompat`` /
``GUID`` TypeDecorators in ``app/core/db_types.py``, which downgrade
gracefully to SQLite-compatible representations (``TEXT``/``JSON``/
``CHAR(36)``) when the runtime dialect is SQLite. This means
``alembic upgrade head`` can run against SQLite for smoke-testing the
migration path, but a handful of PostgreSQL-only conveniences
(server-side ``gen_random_uuid()``, native array containment queries, etc.)
are intentionally not used anywhere in this schema so that both dialects
stay in sync. See docs/TROUBLESHOOTING.md for details.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `app` importable when alembic is invoked from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base  # noqa: E402
from app.core.config import get_settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_db_url() -> str:
    """Pick the sync DB URL, honoring ``ALEMBIC_USE_SQLITE=1`` for tests."""
    if os.environ.get("ALEMBIC_USE_SQLITE") == "1":
        settings = get_settings()
        # Alembic's DDL executor needs a sync driver; swap the async
        # sqlite+aiosqlite DSN used by the app/tests for the sync pysqlite one.
        url = settings.TEST_DATABASE_URL
        if url.startswith("sqlite+aiosqlite"):
            url = url.replace("sqlite+aiosqlite", "sqlite", 1)
        if ":memory:" in url:
            # Alembic needs a durable file to run a real migration against;
            # an in-memory DB would vanish before verification. Use a temp file.
            url = "sqlite:////tmp/smm_alembic_test.db"
        return url
    settings = get_settings()
    return os.environ.get("DATABASE_URL_SYNC", settings.DATABASE_URL_SYNC)


def run_migrations_offline() -> None:
    url = _resolve_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _resolve_db_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
