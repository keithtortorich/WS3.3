"""schedule enqueued_at, analytics uniq, publish job live uniq, mount default_client

Revision ID: e00c25c0041f
Revises: 11bbfaf5a443
Create Date: 2026-07-24 19:28:24.038967

Four related integrity fixes, bundled into one migration deliberately so the
chain stays linear:

1. ``schedules.enqueued_at`` — the enqueue sweep used to overload
   ``is_cancelled`` to mean "already consumed", which made a published schedule
   indistinguishable from a user-cancelled one. GET /api/v1/calendar filters on
   ``is_cancelled``, so published posts silently vanished from the calendar.
2. ``uq_analytics_org_post_captured`` — makes the repository's duplicate-snapshot
   rejection real. Without it, two concurrent pollers both pass the existence
   check and insert twins that double-count in every rollup.
3. ``uq_publish_jobs_live_per_post_account`` — at most one non-terminal publish
   job per (org, post, account), enforced in the database rather than only in the
   sweep's Python-side check.
4. ``integration_mounts.default_client_id`` + ``clients.is_placeholder`` — lets an
   operator bind the real customer once, at mount time, instead of the intent
   path guessing per request; placeholders created by the fallback are flagged so
   they can be listed and merged rather than recognized by name convention.

HAND-EDITED after autogenerate, do not regenerate blindly:
- Added ``import app.core.db_types`` (autogenerate renders ``GUID()`` without it).
- REMOVED autogenerate's ``drop_index`` calls for ``ix_execution_nodes_org_open``
  and ``ix_execution_nodes_org_workflow_ref``. Those are hand-written composites
  from 412a32e37eb2 that are not declared on the ORM model, so every autogenerate
  proposes deleting them. They are intentional — keep them.
- ``clients.is_placeholder`` gets ``server_default=sa.false()``; a NOT NULL column
  added to a table with existing rows fails without one. The default is then
  dropped so the application-side default is the only source going forward.
- Named the ``default_client_id`` foreign key explicitly; autogenerate emitted
  ``drop_constraint(None, ...)`` in downgrade, which cannot execute.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.core.db_types


# revision identifiers, used by Alembic.
revision: str = 'e00c25c0041f'
down_revision: Union[str, None] = '11bbfaf5a443'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('analytics', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_analytics_org_post_captured',
            ['organization_id', 'post_id', 'captured_at'],
        )

    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_placeholder',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.create_index(
            batch_op.f('ix_clients_is_placeholder'), ['is_placeholder'], unique=False
        )
    # Existing rows are backfilled to false by the server_default above; drop it
    # so the Python-side default is the single source of truth from here on.
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.alter_column('is_placeholder', server_default=None)

    with op.batch_alter_table('integration_mounts', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('default_client_id', app.core.db_types.GUID(), nullable=True)
        )
        batch_op.create_index(
            batch_op.f('ix_integration_mounts_default_client_id'),
            ['default_client_id'],
            unique=False,
        )
        batch_op.create_foreign_key(
            'fk_integration_mounts_default_client_id',
            'clients',
            ['default_client_id'],
            ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('publish_jobs', schema=None) as batch_op:
        batch_op.create_index(
            'uq_publish_jobs_live_per_post_account',
            ['organization_id', 'post_id', 'platform_account_id'],
            unique=True,
            postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING', 'RETRYING')"),
            sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING', 'RETRYING')"),
        )

    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('enqueued_at', sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(
            batch_op.f('ix_schedules_enqueued_at'), ['enqueued_at'], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_schedules_enqueued_at'))
        batch_op.drop_column('enqueued_at')

    with op.batch_alter_table('publish_jobs', schema=None) as batch_op:
        batch_op.drop_index(
            'uq_publish_jobs_live_per_post_account',
            postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING', 'RETRYING')"),
            sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING', 'RETRYING')"),
        )

    with op.batch_alter_table('integration_mounts', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_integration_mounts_default_client_id', type_='foreignkey'
        )
        batch_op.drop_index(batch_op.f('ix_integration_mounts_default_client_id'))
        batch_op.drop_column('default_client_id')

    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_clients_is_placeholder'))
        batch_op.drop_column('is_placeholder')

    with op.batch_alter_table('analytics', schema=None) as batch_op:
        batch_op.drop_constraint('uq_analytics_org_post_captured', type_='unique')
