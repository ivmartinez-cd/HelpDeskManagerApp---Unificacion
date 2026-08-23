"""preventivos: coordenadas geocodificadas de sucursal (Fase 2 del mapa)

Revision ID: f4b8e29c6d17
Revises: 9535d6d405c7
Create Date: 2026-08-22 23:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4b8e29c6d17"
down_revision: str | None = "9535d6d405c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "preventivos_sucursal_coordenadas",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("siges_sucursal_id", sa.Integer(), nullable=False),
        sa.Column("latitud", sa.Float(), nullable=False),
        sa.Column("longitud", sa.Float(), nullable=False),
        sa.Column("formatted_address", sa.String(), nullable=False),
        sa.Column(
            "fecha_resolucion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("siges_sucursal_id"),
    )


def downgrade() -> None:
    op.drop_table("preventivos_sucursal_coordenadas")
