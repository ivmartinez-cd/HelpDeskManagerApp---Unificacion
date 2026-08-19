"""liquidaciones geovalidacion Tier 1: cache de reverse geocoding de Georef
por pin redondeado — evita re-consultar el mismo punto (servicio publico
gratuito, sin rate limit publicado pero sin abuso).

Revision ID: b7e3f1a9d2c6
Revises: 9c3e5a71f2d4
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "b7e3f1a9d2c6"
down_revision: str | None = "9c3e5a71f2d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "georef_reverse_cache",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("lat_redondeada", sa.Float(), nullable=False),
        sa.Column("lon_redondeada", sa.Float(), nullable=False),
        sa.Column("provincia_nombre", sa.String(), nullable=True),
        sa.Column("provincia_id", sa.String(), nullable=True),
        sa.Column("departamento_nombre", sa.String(), nullable=True),
        sa.Column("departamento_id", sa.String(), nullable=True),
        sa.Column(
            "fecha_consulta",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "lat_redondeada", "lon_redondeada", name="uq_georef_reverse_cache_pin"
        ),
    )


def downgrade() -> None:
    op.drop_table("georef_reverse_cache")
