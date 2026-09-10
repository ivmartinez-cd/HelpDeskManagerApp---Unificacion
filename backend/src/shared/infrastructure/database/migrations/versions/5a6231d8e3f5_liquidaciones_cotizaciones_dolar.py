"""liquidaciones cotizaciones dolar

Revision ID: 5a6231d8e3f5
Revises: 4cb2bcd2b53d
Create Date: 2026-09-09 21:10:15.934595

Tabla `cotizaciones_dolar` — dólar oficial por período (YYYY-MM), un registro
por mes, para el switch ARS/USD del detalle de liquidación (desde 2026-01 en
adelante). La llena el job `liquidaciones_sync_cotizaciones`
(`SincronizarCotizacionesDolar`), no un seed — arranca vacía.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '5a6231d8e3f5'
down_revision: str | None = '4cb2bcd2b53d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cotizaciones_dolar",
        sa.Column("periodo", sa.String(length=7), primary_key=True),
        sa.Column("compra", sa.Float(), nullable=False),
        sa.Column("venta", sa.Float(), nullable=False),
        sa.Column("fecha_cotizacion", sa.Date(), nullable=False),
        sa.Column("fuente", sa.String(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("cotizaciones_dolar")
