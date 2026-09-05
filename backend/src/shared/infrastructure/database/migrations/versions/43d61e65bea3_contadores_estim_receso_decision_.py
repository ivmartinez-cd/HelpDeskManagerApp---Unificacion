"""contadores_estim_receso_decision_operador

Revision ID: 43d61e65bea3
Revises: a23987343e25
Create Date: 2026-09-05 14:40:59.239932

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "43d61e65bea3"
down_revision: str | None = "a23987343e25"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contadores_decision_operador",
        sa.Column("id_maquina", sa.Integer(), nullable=False),
        sa.Column("clase", sa.String(length=10), nullable=False),
        sa.Column("pendiente", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id_maquina", "clase"),
    )
    op.create_table(
        "contadores_estim_receso",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_grupo_economico", sa.Integer(), nullable=False),
        sa.Column("id_anexo", sa.Integer(), nullable=True),
        sa.Column("fecha_desde", sa.Date(), nullable=False),
        sa.Column("fecha_hasta", sa.Date(), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_contadores_estim_receso_id_grupo_economico"),
        "contadores_estim_receso",
        ["id_grupo_economico"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_contadores_estim_receso_id_grupo_economico"),
        table_name="contadores_estim_receso",
    )
    op.drop_table("contadores_estim_receso")
    op.drop_table("contadores_decision_operador")
