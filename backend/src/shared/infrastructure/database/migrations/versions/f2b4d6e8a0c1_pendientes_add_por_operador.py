"""pendientes: add por_operador column to snapshot

Revision ID: f2b4d6e8a0c1
Revises: e3f5a7c9b1d2
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f2b4d6e8a0c1"
down_revision: str | None = "e3f5a7c9b1d2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "sla_pendientes_snapshot",
        sa.Column(
            "por_operador",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("sla_pendientes_snapshot", "por_operador")
