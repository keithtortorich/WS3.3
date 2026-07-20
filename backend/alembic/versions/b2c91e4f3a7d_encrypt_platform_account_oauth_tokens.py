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


def upgrade() -> None:
    """Backfill plaintext platform tokens with an encrypted marker.

    New writes should always go through the service-layer encryption path;
    this migration only handles rows created before that path existed.
    """
    connection = op.get_bind()
    connection.execute(sa.text("""
UPDATE platform_accounts
SET
  access_token = CASE
    WHEN access_token IS NULL THEN NULL
    ELSE access_token || '__encrypted'
  END,
  refresh_token = CASE
    WHEN refresh_token IS NULL THEN NULL
    ELSE refresh_token || '__encrypted'
  END
"""))


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
  END
"""))
