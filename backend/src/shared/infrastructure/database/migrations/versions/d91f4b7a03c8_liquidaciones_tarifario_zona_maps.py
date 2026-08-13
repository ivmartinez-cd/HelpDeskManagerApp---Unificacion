"""liquidaciones tarifario zona maps

Revision ID: d91f4b7a03c8
Revises: c4d8a91f26e3
Create Date: 2026-08-13

Mapeo por prestador de la zona de Siges (`CostoServicio.descripcion`) a la zona
local del tarifario (ADR-014, dataset 2): los nombres no coinciden literalmente
('General Roca / Rio Negro / Neuquen / Cipoletti' vs 'Gral. Roca / Neuquén') y el
sync no adivina — propone, el usuario confirma, y el mapeo queda persistido acá.
`zona_local` NULL = mapeada a la zona genérica (tarifario sin zona): es el caso
mayoritario real — la descripción de la mayoría de los PSTs es su código de
tarifa TMT* y corresponde al grupo local sin zona.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d91f4b7a03c8"
down_revision: str | None = "c4d8a91f26e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tarifario_zona_maps",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("descripcion_siges", sa.String(), nullable=False),
        sa.Column("zona_local", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestadores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "prestador_id", "descripcion_siges", name="uq_tarifario_zona_maps_prestador_desc"
        ),
    )


def downgrade() -> None:
    op.drop_table("tarifario_zona_maps")
