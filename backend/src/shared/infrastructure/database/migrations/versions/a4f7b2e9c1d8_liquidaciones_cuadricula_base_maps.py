"""liquidaciones cuadricula base maps

Revision ID: a4f7b2e9c1d8
Revises: 9f5d525c7c23
Create Date: 2026-08-16

Mapeo por prestador de la cuadrícula de Siges (Sucursal.Cuadricula, visible
como "Cod. Agrupación" en Gestión) a la sucursal-base propia del PST usada como
punto de origen en el cálculo de distancias. Permite que PSTs con múltiples
técnicos en distintas sedes asignen el origen correcto por grupo de clientes sin
intervención manual por fila."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a4f7b2e9c1d8"
down_revision: str | None = "b2f7d914ce08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cuadricula_base_maps",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("cuadricula", sa.String(), nullable=False),
        sa.Column("siges_base_sucursal_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestadores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "prestador_id", "cuadricula", name="uq_cuadricula_base_maps_prestador_cuadricula"
        ),
    )


def downgrade() -> None:
    op.drop_table("cuadricula_base_maps")
