"""liquidaciones matching sucursales: tabla de descartes de candidatos N2
(Tabla KM ↔ Siges) — decisión 0.4.d del plan de matching de sucursales, un
rechazo se recuerda y no vuelve a proponerse.

Revision ID: 9c3e5a71f2d4
Revises: b1e6f4a2c8d3
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "9c3e5a71f2d4"
down_revision: str | None = "b1e6f4a2c8d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "matching_descartes_tabla_km",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tabla_km_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tabla_kms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("siges_sucursal_id", sa.Integer(), nullable=False),
        sa.Column("usuario_email", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tabla_km_id", "siges_sucursal_id", name="uq_matching_descarte_fila_candidato"
        ),
    )
    op.create_index(
        "ix_matching_descartes_tabla_km_id", "matching_descartes_tabla_km", ["tabla_km_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_matching_descartes_tabla_km_id", table_name="matching_descartes_tabla_km")
    op.drop_table("matching_descartes_tabla_km")
