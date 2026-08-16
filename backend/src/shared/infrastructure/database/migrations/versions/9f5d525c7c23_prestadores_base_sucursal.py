"""prestadores_base_sucursal

Revision ID: 9f5d525c7c23
Revises: c2e5f8a3d9b1
Create Date: 2026-08-15 19:48:39.070373

El autogenerate original traía falsos positivos (alter_columns y drops de
tablas de otros módulos, por metadata no importada en el env) — se eliminó
todo: esta migración solo agrega la columna de base de despacho.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9f5d525c7c23"
down_revision: str | None = "c2e5f8a3d9b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "prestadores", sa.Column("siges_base_sucursal_id", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("prestadores", "siges_base_sucursal_id")
