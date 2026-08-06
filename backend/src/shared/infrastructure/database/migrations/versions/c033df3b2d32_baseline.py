"""baseline

Revision ID: c033df3b2d32
Revises: 
Create Date: 2026-08-06 11:44:40.684616

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'c033df3b2d32'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
