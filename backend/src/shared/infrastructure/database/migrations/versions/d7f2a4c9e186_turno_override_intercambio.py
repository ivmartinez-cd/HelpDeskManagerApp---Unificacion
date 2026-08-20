"""turno asignacion override -- intercambio_id (ADR-026)

Revision ID: d7f2a4c9e186
Revises: c5e1a7d3b902
Create Date: 2026-08-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7f2a4c9e186"
down_revision: str | None = "c5e1a7d3b902"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "turno_asignacion_override",
        sa.Column("intercambio_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        "ix_turno_asignacion_override_intercambio_id",
        "turno_asignacion_override",
        ["intercambio_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_turno_asignacion_override_intercambio_id", table_name="turno_asignacion_override"
    )
    op.drop_column("turno_asignacion_override", "intercambio_id")
