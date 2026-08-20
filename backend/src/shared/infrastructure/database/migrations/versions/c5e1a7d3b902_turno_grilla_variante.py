"""turno grilla variante -- modo vacaciones (ADR-025)

Revision ID: c5e1a7d3b902
Revises: b3d7c2a9e451
Create Date: 2026-08-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c5e1a7d3b902"
down_revision: str | None = "b3d7c2a9e451"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "turno_grilla_variante",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("motivo", sa.String(length=200), nullable=True),
        sa.Column("origen_texto", sa.String(length=200), nullable=True),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="ACTIVA", nullable=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("desde <= hasta", name="ck_grilla_variante_rango_valido"),
        sa.CheckConstraint(
            "estado IN ('ACTIVA', 'CANCELADA')", name="ck_grilla_variante_estado"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_grilla_variante_estado_vigencia",
        "turno_grilla_variante",
        ["estado", "desde", "hasta"],
    )
    op.create_table(
        "turno_grilla_variante_slot",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("variante_id", sa.UUID(), nullable=False),
        sa.Column("casilla_id", sa.UUID(), nullable=False),
        sa.Column("dia_semana", sa.SmallInteger(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(
            ["variante_id"], ["turno_grilla_variante.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["casilla_id"], ["turno_casilla.id"], ondelete="CASCADE"),
        sa.CheckConstraint("hora_inicio < hora_fin", name="ck_grilla_variante_slot_horas"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_grilla_variante_slot_variante", "turno_grilla_variante_slot", ["variante_id"]
    )
    op.create_table(
        "turno_grilla_variante_asignacion",
        sa.Column("variante_slot_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["variante_slot_id"], ["turno_grilla_variante_slot.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("variante_slot_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("turno_grilla_variante_asignacion")
    op.drop_index("ix_grilla_variante_slot_variante", table_name="turno_grilla_variante_slot")
    op.drop_table("turno_grilla_variante_slot")
    op.drop_index("ix_grilla_variante_estado_vigencia", table_name="turno_grilla_variante")
    op.drop_table("turno_grilla_variante")
