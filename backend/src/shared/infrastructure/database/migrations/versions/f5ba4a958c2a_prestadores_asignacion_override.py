"""prestadores asignacion override (ADR-013)

Revision ID: f5ba4a958c2a
Revises: 7fa2e507b087
Create Date: 2026-08-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f5ba4a958c2a"
down_revision: str | None = "7fa2e507b087"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prestador_asignacion_override",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("operador_ausente_id", sa.UUID(), nullable=False),
        sa.Column("operador_reemplazante_id", sa.UUID(), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=False),
        sa.Column("alcance_total", sa.Boolean(), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="ACTIVA", nullable=False),
        sa.Column("motivo", sa.String(length=200), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["operador_ausente_id"], ["app_user.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["operador_reemplazante_id"], ["app_user.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["app_user.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint("desde <= hasta", name="ck_override_rango_valido"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "prestador_asignacion_override_prestador",
        sa.Column("override_id", sa.UUID(), nullable=False),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["override_id"], ["prestador_asignacion_override.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestador.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("override_id", "prestador_id"),
    )


def downgrade() -> None:
    op.drop_table("prestador_asignacion_override_prestador")
    op.drop_table("prestador_asignacion_override")
