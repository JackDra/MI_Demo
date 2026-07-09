"""add river section percent filled

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-09 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("river_section", sa.Column("percent_filled", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("river_section", "percent_filled")
