"""sla snapshot schema

Revision ID: 4c8989f23439
Revises: ac5e139e28b4
Create Date: 2026-08-12 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "4c8989f23439"
down_revision: str | None = "ac5e139e28b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sla_periodo_snapshot",
        sa.Column("periodo", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("correctos", sa.Integer(), nullable=False),
        sa.Column("vencidos", sa.Integer(), nullable=False),
        sa.Column("pct_correctos", sa.Float(), nullable=False),
        sa.Column("pct_vencidos", sa.Float(), nullable=False),
        sa.Column("vencidos_por_tecnico", JSONB(), nullable=False),
        sa.Column("incidentes_vencidos", JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("periodo"),
    )


def downgrade() -> None:
    op.drop_table("sla_periodo_snapshot")
