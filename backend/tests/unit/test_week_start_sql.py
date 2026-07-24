"""Compile-level guard for the cross-dialect ISO-week bucket.

The test suite runs on SQLite, so a PostgreSQL-only regression in
``week_start`` would otherwise ship green. These tests assert on the
*emitted SQL text* for both dialects.

The ``AT TIME ZONE 'UTC'`` assertion is not cosmetic: without it,
PostgreSQL's ``date_trunc('week', <timestamptz>)`` truncates in the session
TimeZone, so a Sunday-23:00Z snapshot buckets into the following week on a
server configured to any positive UTC offset (reproduced against a real
PostgreSQL 18.4 with TimeZone=Asia/Manila).
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite

from app.core.sql_functions import week_start
from app.models.analytics import Analytics


def _compiled(dialect) -> str:
    stmt = select(week_start(Analytics.captured_at).label("week_start"))
    return str(stmt.compile(dialect=dialect))


def test_postgresql_week_bucket_is_utc_normalized():
    sql = _compiled(postgresql.dialect())
    assert "date_trunc('week'" in sql
    assert "AT TIME ZONE 'UTC'" in sql
    assert "AS DATE" in sql


def test_sqlite_week_bucket_uses_weekday_shift():
    sql = _compiled(sqlite.dialect())
    assert "DATE(analytics.captured_at, '-6 days', 'weekday 1')" in sql


def test_unsupported_dialect_fails_loudly():
    from sqlalchemy.dialects import mysql

    with pytest.raises(NotImplementedError):
        _compiled(mysql.dialect())
