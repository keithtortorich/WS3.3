"""merge seed_marketing_agents and oauth_token_encryption branches

Revision ID: a1b4bb27ec5c
Revises: 6c2bff6f48c0, d3f10a7c9b11
Create Date: 2026-07-24 04:58:31.877753

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b4bb27ec5c'
down_revision: Union[str, None] = ('6c2bff6f48c0', 'd3f10a7c9b11')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
