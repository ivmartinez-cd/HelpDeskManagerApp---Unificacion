"""tabla_km coordenadas destino

Revision ID: a1b2c3d4e5f6
Revises: 9f5d525c7c23
Create Date: 2026-08-15

Agrega latitud_destino y longitud_destino a tabla_kms para poder mostrar
un link de validación visual de la dirección del cliente contra Google Maps.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "9f5d525c7c23"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tabla_kms", sa.Column("latitud_destino", sa.Float(), nullable=True))
    op.add_column("tabla_kms", sa.Column("longitud_destino", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("tabla_kms", "longitud_destino")
    op.drop_column("tabla_kms", "latitud_destino")
