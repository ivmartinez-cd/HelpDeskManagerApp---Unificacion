"""preventivos schema (habilitaciones locales)

Revision ID: b3f1c9a7d2e4
Revises: e2a86d47f1b9
Create Date: 2026-08-14 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3f1c9a7d2e4"
down_revision: str | None = "e2a86d47f1b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "preventivos_habilitacion",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("siges_maquina_id", sa.Integer(), nullable=False),
        sa.Column("habilitado_por_user_id", sa.UUID(), nullable=False),
        sa.Column("habilitado_por_nombre", sa.String(length=120), nullable=False),
        sa.Column(
            "habilitado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("nota", sa.String(length=300), nullable=True),
        sa.Column("activa", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("deshabilitado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deshabilitado_por", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(
            ["habilitado_por_user_id"], ["app_user.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # A lo sumo UNA habilitación activa por máquina; las desactivadas quedan
    # como historial de auditoría.
    op.create_index(
        "uq_preventivos_habilitacion_activa",
        "preventivos_habilitacion",
        ["siges_maquina_id"],
        unique=True,
        postgresql_where=sa.text("activa"),
    )


def downgrade() -> None:
    op.drop_index("uq_preventivos_habilitacion_activa", table_name="preventivos_habilitacion")
    op.drop_table("preventivos_habilitacion")
