"""liquidaciones: backfill tipo_liquidacion='abono'

Revision ID: a9c4e2f7b1d3
Revises: 642ff851091c
Create Date: 2026-09-05

Marca como `abono` toda liquidación cuyos incidentes están TODOS a $1 de costo de
servicio (contrato mensual de SAN JUAN, importe real en el ítem extra — ver
`domain/services/tipo_abono.py`). Absorbe también los dos tipos del CSV legacy
(`cc`/`preco`, ambos con este mismo patrón). Sin esto, las 31 liquidaciones
existentes seguirían corriendo las reglas de precio por incidente en cada
reanálisis. Idempotente. El downgrade vuelve todas a `regular` (los `cc`/`preco`
originales no se restauran: eran el mismo concepto con otro nombre).
"""

import sqlalchemy as sa
from alembic import op

revision = "a9c4e2f7b1d3"
down_revision = "642ff851091c"
branch_labels = None
depends_on = None

_UPGRADE = """
UPDATE liquidaciones l
SET tipo_liquidacion = 'abono'
WHERE l.total_incidentes > 0
  AND l.tipo_liquidacion <> 'abono'
  AND NOT EXISTS (
      SELECT 1 FROM incidentes i
      WHERE i.liquidacion_id = l.id AND i.costo_servicio_cobrado <> 1
  )
  AND EXISTS (SELECT 1 FROM incidentes i WHERE i.liquidacion_id = l.id)
"""


def upgrade() -> None:
    op.get_bind().execute(sa.text(_UPGRADE))


def downgrade() -> None:
    op.get_bind().execute(
        sa.text(
            "UPDATE liquidaciones SET tipo_liquidacion = 'regular' WHERE tipo_liquidacion = 'abono'"
        )
    )
