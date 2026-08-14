"""pendientes snapshot schema

Revision ID: e3f5a7c9b1d2
Revises: d1a7f3c8e5b2
Create Date: 2026-08-14 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "e3f5a7c9b1d2"
down_revision: str | None = "d1a7f3c8e5b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sla_pendientes_snapshot",
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("incidentes", JSONB(), nullable=False),
        sa.Column("por_prestador", JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("version"),
    )


def downgrade() -> None:
    op.drop_table("sla_pendientes_snapshot")
