"""contadores_decision_operador_valor_manual

Revision ID: 642ff851091c
Revises: 43d61e65bea3
Create Date: 2026-09-05 15:40:55.324114

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "642ff851091c"
down_revision: str | None = "43d61e65bea3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contadores_decision_operador",
        sa.Column("manual_contador_propuesto", sa.Numeric(precision=18, scale=2), nullable=True),
    )
    op.add_column(
        "contadores_decision_operador",
        sa.Column("manual_tipo_toma", sa.Integer(), nullable=True),
    )
    op.add_column(
        "contadores_decision_operador",
        sa.Column("manual_fuente", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "contadores_decision_operador",
        sa.Column("manual_metodo_detalle", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("contadores_decision_operador", "manual_metodo_detalle")
    op.drop_column("contadores_decision_operador", "manual_fuente")
    op.drop_column("contadores_decision_operador", "manual_tipo_toma")
    op.drop_column("contadores_decision_operador", "manual_contador_propuesto")
