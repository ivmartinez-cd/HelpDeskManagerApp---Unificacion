"""calculo_km_previews: agregar sin_actividad.

Cuenta cuántas sucursales de Siges fueron descartadas por no tener actividad
reciente (sin incidentes en los últimos 24 meses). Solo se usa para mostrar
el badge en el UI — no afecta el apply.

Revision ID: e4f8b3c9a2d1
Revises: d3e9f4a2c5b8
Create Date: 2026-08-16
"""

import sqlalchemy as sa
from alembic import op

revision = "e4f8b3c9a2d1"
down_revision = "d3e9f4a2c5b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "calculo_km_previews",
        sa.Column("sin_actividad", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("calculo_km_previews", "sin_actividad")
