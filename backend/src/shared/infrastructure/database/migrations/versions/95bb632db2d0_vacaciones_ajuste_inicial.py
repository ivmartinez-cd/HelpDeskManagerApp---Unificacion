"""vacaciones: ajuste de carga inicial separado de los días por antigüedad

Revision ID: 95bb632db2d0
Revises: a9d4e6b3c2f1
Create Date: 2026-10-09

Los ciclos 2026 vinieron de la planilla de RRHH importada al legacy, que
guardaba en `annual_days` el saldo anotado (días por antigüedad menos lo ya
tomado antes del sistema, más lo arrastrado de 2025), no los días que
corresponden. La UI mostraba "14/21" a quien le corresponden 35.

Se agrega `ajuste_inicial` y, en cada ciclo 2026 cuyo `annual_days` difiere de
la tabla de antigüedad, se pasa a `annual_days` = días por regla y
`ajuste_inicial` = anotado − regla. El disponible no cambia.

Excepción: el ingreso del año (ingresó después del 1/1) con `annual_days` igual
al último tier es el bug del legacy, no un dato anotado: se corrige a la regla
(primer tier) sin ajuste. Su disponible baja. El downgrade no lo restaura.

La regla replica `dias_por_antiguedad` (365.25, min inclusive / max exclusivo,
debajo del primer tier → primer tier, arriba del último → último). Idempotente.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "95bb632db2d0"
down_revision: str | None = "a9d4e6b3c2f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BACKFILL = """
WITH t AS (
    SELECT (x->>'min_years')::numeric AS mn,
           (x->>'max_years')::numeric AS mx,
           (x->>'days')::int AS d
    FROM vacaciones_config, jsonb_array_elements(seniority_tiers) AS x
    WHERE id = 'singleton'
),
c AS (
    SELECT c.id, c.annual_days,
           e.hire_date > make_date(c.year, 1, 1) AS ingreso_del_anio,
           (make_date(c.year, 1, 1) - e.hire_date) / 365.25 AS anios
    FROM vacaciones_ciclo c
    JOIN vacaciones_empleado e ON e.id = c.empleado_id
    WHERE c.year = 2026
),
r AS (
    SELECT c.id, c.annual_days, c.ingreso_del_anio,
           (SELECT d FROM t ORDER BY mn DESC LIMIT 1) AS ultimo,
           COALESCE(
               CASE WHEN c.anios < (SELECT min(mn) FROM t)
                    THEN (SELECT d FROM t ORDER BY mn LIMIT 1) END,
               (SELECT d FROM t WHERE c.anios >= mn AND c.anios < mx ORDER BY mn LIMIT 1),
               (SELECT d FROM t ORDER BY mn DESC LIMIT 1)
           ) AS regla
    FROM c
)
UPDATE vacaciones_ciclo v
SET ajuste_inicial = CASE
        WHEN r.ingreso_del_anio AND r.annual_days = r.ultimo THEN 0
        ELSE r.annual_days - r.regla
    END,
    annual_days = r.regla
FROM r
WHERE v.id = r.id
  AND r.regla IS NOT NULL
  AND v.annual_days <> r.regla
"""

_REVERTIR = """
UPDATE vacaciones_ciclo
SET annual_days = annual_days + ajuste_inicial
WHERE ajuste_inicial <> 0
"""


def upgrade() -> None:
    op.add_column(
        "vacaciones_ciclo",
        sa.Column("ajuste_inicial", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.get_bind().execute(sa.text(_BACKFILL))


def downgrade() -> None:
    op.get_bind().execute(sa.text(_REVERTIR))
    op.drop_column("vacaciones_ciclo", "ajuste_inicial")
