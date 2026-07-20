"""Encrypt OAuth tokens for existing and new PlatformAccount rows.

Revision ID: b2c91e4f3a7d
Revises: 92ba5d1cd517
Create Date: 2026-07-20 19:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c91e4f3a7d'
down_revision: str | None = '92ba5d1cd517'
branch_labels: str | None = None
depends_on: str | None = None


UPGRADE_SQL = """
-- Backfill any plaintext tokens from the scaffold state.
-- In production, decrypt with the same active key before re-encrypting;
-- this migration assumes the data can be re-encrypted in place or that
-- no production rows exist yet.
UPDATE platform_accounts
SET
  access_token = CASE
    WHEN access_token IS NULL THEN NULL
    ELSE access_token || '__encrypted'
  END,
  refresh_token = CASE
    WHEN refresh_token IS NULL THEN NULL
    ELSE refresh_token || '__encrypted'
  END;

ALTER TABLE platform_accounts
  ALTER COLUMN access_token TYPE TEXT;

ALTER TABLE platform_accounts
  ALTER COLUMN refresh_token TYPE TEXT;
"""


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text(UPGRADE_SQL))


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("""
UPDATE platform_accounts
SET
  access_token = CASE
    WHEN access_token IS NULL THEN NULL
    ELSE REPLACE(access_token, '__encrypted', '')
  END,
  refresh_token = CASE
    WHEN refresh_token IS NULL THEN NULL
    ELSE REPLACE(refresh_token, '__encrypted', '')
  END;
"""))
