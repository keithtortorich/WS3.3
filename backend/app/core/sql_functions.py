"""Cross-dialect SQL expression helpers.

Same motivation as ``app/core/db_types.py``: production runs on PostgreSQL
while the test suite runs on SQLite, and a handful of PostgreSQL-native
constructs have no direct SQLite equivalent. ``db_types`` solves that for
*column types*; this module solves it for *expressions*.

Currently one construct: :class:`week_start`, the ISO-week bucket used by
the weekly KPI rollup (``docs/sql/smm_gtm_bridge.sql`` section 4b, which is
written Postgres-only as ``date_trunc('week', ...)::date``).

Both dialects produce the **Monday, in UTC,** of the week containing the
argument, as a DATE:

* PostgreSQL: ``date_trunc('week', ts AT TIME ZONE 'UTC')`` — Monday-based.
  The ``AT TIME ZONE 'UTC'`` is load-bearing, not decoration: applied to a
  ``timestamptz``, bare ``date_trunc('week', ts)`` truncates in the
  *session* TimeZone, so the same row buckets into different weeks
  depending on server configuration. Verified against a real PostgreSQL
  18.4 server with ``TimeZone = Asia/Manila``: a snapshot at
  ``2026-01-11 23:00Z`` (a Sunday) was bucketed into the week of
  ``2026-01-12`` because it is Monday 07:00 local. With the cast to UTC it
  buckets to ``2026-01-05``, matching SQLite. Assumes the argument is a
  ``timestamptz`` (every ``captured_at``-style column in this schema is
  ``DateTime(timezone=True)``).
* SQLite: ``DATE(ts, '-6 days', 'weekday 1')`` — shift back 6 days, then
  advance to the next Monday (``weekday 1`` is a no-op when the date is
  already a Monday). For any day Mon..Sun this lands on the Monday of that
  same ISO week. SQLite stores these columns as naive UTC, so no timezone
  handling is needed on that side.

Any other dialect raises at compile time rather than silently emitting
something wrong.
"""
from __future__ import annotations

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.types import Date


class week_start(FunctionElement):  # noqa: N801 - SQL construct, lowercase by convention
    """ISO-week (Monday) start date of a timestamp column, as a DATE."""

    type = Date()
    name = "week_start"
    inherit_cache = True


@compiles(week_start)
def _week_start_default(element, compiler, **kw):  # pragma: no cover - guard
    raise NotImplementedError(
        f"week_start() has no implementation for dialect "
        f"{compiler.dialect.name!r}; add one in app/core/sql_functions.py."
    )


@compiles(week_start, "postgresql")
def _week_start_postgresql(element, compiler, **kw) -> str:
    (arg,) = element.clauses
    return (
        "CAST(date_trunc('week', "
        f"{compiler.process(arg, **kw)} AT TIME ZONE 'UTC') AS DATE)"
    )


@compiles(week_start, "sqlite")
def _week_start_sqlite(element, compiler, **kw) -> str:
    (arg,) = element.clauses
    return f"DATE({compiler.process(arg, **kw)}, '-6 days', 'weekday 1')"
