"""preventivos: auditoría de corrección manual en sucursal_coordenadas

Revision ID: a3e7c1f92b48
Revises: b7d2f9a4c6e1
Create Date: 2026-08-23 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a3e7c1f92b48"
down_revision: str | None = "b7d2f9a4c6e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "preventivos_sucursal_coordenadas",
        sa.Column(
            "corregido_por_user_id",
            sa.UUID(),
            sa.ForeignKey("app_user.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "preventivos_sucursal_coordenadas",
        sa.Column("corregido_por_nombre", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "preventivos_sucursal_coordenadas",
        sa.Column("nota", sa.String(length=300), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preventivos_sucursal_coordenadas", "nota")
    op.drop_column("preventivos_sucursal_coordenadas", "corregido_por_nombre")
    op.drop_column("preventivos_sucursal_coordenadas", "corregido_por_user_id")
