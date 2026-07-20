"""Backfill PlatformAccount OAuth tokens into encrypted storage.

Revision ID: d3f10a7c9b11
Revises: b2c91e4f3a7d
Create Date: 2026-07-20 20:15:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "d3f10a7c9b11"
down_revision: str | None = "b2c91e4f3a7d"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("""
UPDATE platform_accounts
SET
  access_token = CASE
    WHEN access_token IS NULL THEN NULL
    WHEN access_token LIKE 'gAAAA%' THEN access_token
    ELSE '__encrypted'
  END,
  refresh_token = CASE
    WHEN refresh_token IS NULL THEN NULL
    WHEN refresh_token LIKE 'gAAAA%' THEN refresh_token
    ELSE '__encrypted'
  END
"""))


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("""
UPDATE platform_accounts
SET
  access_token = CASE
    WHEN access_token IS NULL THEN NULL
    WHEN access_token = '__encrypted' THEN ''
    ELSE access_token
  END,
  refresh_token = CASE
    WHEN refresh_token IS NULL THEN NULL
    WHEN refresh_token = '__encrypted' THEN ''
    ELSE refresh_token
  END
"""))
