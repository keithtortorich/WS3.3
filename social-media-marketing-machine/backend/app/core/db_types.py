"""Cross-dialect column types.

The scaffold must run against both PostgreSQL (production, via asyncpg /
psycopg) and SQLite (aiosqlite, for the fast unit/integration test suite —
see backend/tests/). A handful of PostgreSQL-native types (UUID, JSONB,
ARRAY) have no direct SQLite equivalent, so we provide small
``TypeDecorator`` shims that pick the native type on Postgres and a
lowest-common-denominator (CHAR(36) / TEXT+JSON) representation on SQLite.

This is the officially documented SQLAlchemy pattern for "Backend-agnostic
GUID Type" (see SQLAlchemy docs: "Backend-agnostic GUID Type" cookbook
recipe), extended here with a JSON-ish column for our few JSONB-typed
columns so the same model works unmodified on both dialects.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import CHAR, TEXT, TypeDecorator, TypeEngine


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native UUID type when available, otherwise stores as
    a stringified CHAR(36) (SQLite has no native UUID type).
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Optional[Any], dialect) -> Optional[str]:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(str(value)))
        return str(value)

    def process_result_value(self, value: Optional[Any], dialect) -> Optional[uuid.UUID]:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class JSONBCompat(TypeDecorator):
    """JSONB on PostgreSQL, plain JSON (TEXT-backed) on SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class StringArrayCompat(TypeDecorator):
    """ARRAY(String) on PostgreSQL, JSON-encoded TEXT list on SQLite.

    Used for small tag-like lists (e.g. keywords, hashtags) where a full
    association table would be overkill for a scaffold.
    """

    impl = TEXT
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(TEXT()))
        return dialect.type_descriptor(TEXT())

    def process_bind_param(self, value: Optional[Any], dialect) -> Optional[Any]:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(list(value))

    def process_result_value(self, value: Optional[Any], dialect) -> Optional[list]:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value)
        return json.loads(value)
