"""app user color

Revision ID: 4f7c614dafe3
Revises: 22de345a0251
Create Date: 2026-08-12 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4f7c614dafe3"
down_revision: str | None = "22de345a0251"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("color", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("app_user", "color")
