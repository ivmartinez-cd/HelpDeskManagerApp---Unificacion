"""tabla_kms: columna archivada + backfill de filas sin actividad en 2026

Revision ID: c3e8f1a9d2b4
Revises: b7d1e9a3c5f2
Create Date: 2026-09-05

De 2.748 filas de Tabla KM, solo 1.229 fueron usadas por alguna liquidación de
2026. Las demás se archivan (no se borran: el motor las sigue resolviendo si
la sucursal reaparece) para que la pantalla muestre lo que importa. Match por
el mismo par empresa+sucursal normalizado que usa el motor.
"""

import sqlalchemy as sa
from alembic import op

revision = "c3e8f1a9d2b4"
down_revision = "b7d1e9a3c5f2"
branch_labels = None
depends_on = None

_BACKFILL = """
UPDATE tabla_kms k SET archivada = true
WHERE NOT EXISTS (
    SELECT 1 FROM incidentes i
    JOIN liquidaciones l ON l.id = i.liquidacion_id
    WHERE l.prestador_id = k.prestador_id
      AND l.periodo >= '2026-01'
      AND lower(trim(i.empresa_nombre)) = lower(trim(k.empresa_nombre))
      AND lower(trim(i.sucursal_nombre)) = lower(trim(k.sucursal_nombre))
)
"""


def upgrade() -> None:
    op.add_column(
        "tabla_kms",
        sa.Column("archivada", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.get_bind().execute(sa.text(_BACKFILL))


def downgrade() -> None:
    op.drop_column("tabla_kms", "archivada")
