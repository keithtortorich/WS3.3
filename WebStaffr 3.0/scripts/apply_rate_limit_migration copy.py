#!/usr/bin/env python3
"""Apply 0005_rate_limit_counters.sql to live Postgres.
Reads DATABASE_URL from env or CREDENTIALS.md first unindented value.
Never prints the raw URL.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

def _find_database_url() -> str:
    env = os.environ.get("DATABASE_URL")
    if env:
        return env
    creds = Path(__file__).resolve().parent.parent / "CREDENTIALS.md"
    if creds.exists():
        for line in creds.read_text().splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1]
    sys.exit("DATABASE_URL not found")

def main() -> None:
    database_url = _find_database_url()
    sql_path = (
        Path(__file__).resolve().parent.parent
        / "webstaffr" / "migrations" / "postgres_manual" / "0005_rate_limit_counters.sql"
    )
    sql = sql_path.read_text()

    import psycopg2
    conn = psycopg2.connect(database_url)
    try:
        conn.cursor().execute(sql)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        sys.exit(f"ERROR: {exc}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
