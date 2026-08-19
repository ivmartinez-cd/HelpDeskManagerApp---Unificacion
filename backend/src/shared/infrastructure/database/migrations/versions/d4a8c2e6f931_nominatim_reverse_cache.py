"""liquidaciones geovalidacion Tier 1b: cache de reverse geocoding de
Nominatim por pin redondeado -- obligatoria por la politica de uso del
servicio (no solo cortesia como con Georef).

Revision ID: d4a8c2e6f931
Revises: b7e3f1a9d2c6
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "d4a8c2e6f931"
down_revision: str | None = "b7e3f1a9d2c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nominatim_reverse_cache",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("lat_redondeada", sa.Float(), nullable=False),
        sa.Column("lon_redondeada", sa.Float(), nullable=False),
        sa.Column("provincia_nombre", sa.String(), nullable=True),
        sa.Column(
            "fecha_consulta",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "lat_redondeada", "lon_redondeada", name="uq_nominatim_reverse_cache_pin"
        ),
    )


def downgrade() -> None:
    op.drop_table("nominatim_reverse_cache")
