"""contadores_estim_log_auditoria

Revision ID: a23987343e25
Revises: b7e4d9a2c531
Create Date: 2026-09-05 04:02:49.070824

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a23987343e25"
down_revision: str | None = "b7e4d9a2c531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contadores_estim_log",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("operador_user_id", sa.UUID(), nullable=True),
        sa.Column("operador_email", sa.String(length=255), nullable=False),
        sa.Column("nro_proceso", sa.Integer(), nullable=True),
        sa.Column("id_maquina", sa.Integer(), nullable=False),
        sa.Column("clase", sa.String(length=10), nullable=False),
        sa.Column("accion", sa.String(length=30), nullable=False),
        sa.Column("fecha_objetivo", sa.Date(), nullable=True),
        sa.Column("contador_anterior", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("contador_propuesto", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("tipo_toma_grabado", sa.Integer(), nullable=True),
        sa.Column("fuente", sa.String(length=40), nullable=True),
        sa.Column("metodo_detalle", sa.String(length=200), nullable=True),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("detalle", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["operador_user_id"], ["app_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contadores_estim_log_maquina_clase",
        "contadores_estim_log",
        ["id_maquina", "clase"],
    )


def downgrade() -> None:
    op.drop_index("ix_contadores_estim_log_maquina_clase", table_name="contadores_estim_log")
    op.drop_table("contadores_estim_log")
