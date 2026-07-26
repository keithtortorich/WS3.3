#!/usr/bin/env python3
"""Read-only Supabase/Postgres connection diagnostic for WS3.3.

Reads DATABASE_URL from the environment or, if unset, prompts on stdin.
Does not write, log, or echo the secret after reading it.
Prints only one of:
  SUCCESS
  SUCCESS_NO_DATA
  FAILED: <short reason>
"""
from __future__ import annotations

import os
import sys

def read_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    try:
        url = input("DATABASE_URL: ")
    except EOFError:
        url = ""
    return url.strip()

def main() -> None:
    url = read_url()
    if not url:
        print("FAILED: DATABASE_URL is empty")
        sys.exit(1)

    try:
        import psycopg2  # type: ignore[import-untyped]
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: psycopg2 import error: {exc}")
        sys.exit(1)

    try:
        conn = psycopg2.connect(url, connect_timeout=10)
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: connection error: {exc}")
        sys.exit(1)

    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
            if row and row[0] == 1:
                print("SUCCESS")
            else:
                print("FAILED: unexpected query result")
                sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: query error: {exc}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
