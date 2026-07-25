"""Seed marketing agents

Revision ID: 6c2bff6f48c0
Revises: 92ba5d1cd517
Create Date: 2026-07-22 07:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.core.db_types


revision: str = "6c2bff6f48c0"
down_revision: Union[str, None] = "92ba5d1cd517"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_templates",
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("template_body", sa.Text(), nullable=False),
        sa.Column("variables", app.core.db_types.StringArrayCompat(), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", app.core.db_types.GUID(), nullable=False),
        sa.Column("organization_id", app.core.db_types.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "slug", "version", name="uq_agent_template_org_slug_version"
        ),
    )
    with op.batch_alter_table("agent_templates", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_agent_templates_category"), ["category"], unique=False)
        batch_op.create_index(batch_op.f("ix_agent_templates_organization_id"), ["organization_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_agent_templates_slug"), ["slug"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("agent_templates", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_agent_templates_slug"), unique=False)
        batch_op.drop_index(batch_op.f("ix_agent_templates_organization_id"), unique=False)
        batch_op.drop_index(batch_op.f("ix_agent_templates_category"), unique=False)

    op.drop_table("agent_templates")
