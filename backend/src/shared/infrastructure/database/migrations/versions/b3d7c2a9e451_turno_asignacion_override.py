"""turno asignacion override (ADR-013)

Revision ID: b3d7c2a9e451
Revises: a1c9f4e7b358
Create Date: 2026-08-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3d7c2a9e451"
down_revision: str | None = "a1c9f4e7b358"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "turno_asignacion_override",
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
        "turno_asignacion_override_slot",
        sa.Column("override_id", sa.UUID(), nullable=False),
        sa.Column("slot_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["override_id"], ["turno_asignacion_override.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["slot_id"], ["turno_slot.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("override_id", "slot_id"),
    )


def downgrade() -> None:
    op.drop_table("turno_asignacion_override_slot")
    op.drop_table("turno_asignacion_override")
