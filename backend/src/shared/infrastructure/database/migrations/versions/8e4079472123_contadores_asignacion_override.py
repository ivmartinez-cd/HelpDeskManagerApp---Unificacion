"""contadores asignacion override (ADR-013)

Revision ID: 8e4079472123
Revises: f5ba4a958c2a
Create Date: 2026-08-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8e4079472123"
down_revision: str | None = "f5ba4a958c2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contadores_asignacion_override",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("operador_ausente_id", sa.String(), nullable=False),
        sa.Column("operador_reemplazante_id", sa.String(), nullable=False),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("vigente_hasta", sa.Date(), nullable=False),
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
            ["created_by_user_id"], ["app_user.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint("vigente_desde <= vigente_hasta", name="ck_calendar_override_rango"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "contadores_asignacion_override_cliente",
        sa.Column("override_id", sa.UUID(), nullable=False),
        sa.Column("cliente", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["override_id"], ["contadores_asignacion_override.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("override_id", "cliente"),
    )


def downgrade() -> None:
    op.drop_table("contadores_asignacion_override_cliente")
    op.drop_table("contadores_asignacion_override")
