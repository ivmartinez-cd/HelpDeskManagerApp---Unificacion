"""seed liquidaciones reglas alerta

Revision ID: 17663a83c3fd
Revises: 2d3c7ac61eeb
Create Date: 2026-08-13 08:57:44.026245

Siembra el catálogo de 9 reglas del motor (`ALT001`-`ALT009`), transcripto de
`seed_reglas()` del legacy (`Liquidacion-Prestadores/backend/seed.py`). Sin
esta tabla poblada, `motor_reglas/motor.py` no encuentra ninguna regla activa
y no genera alertas — el motor está portado pero queda inerte.

`activa` NO usa el default de `seed.py` (que trae `ALT005`/`ALT006`/`ALT007`
en `False`): se sembró con el estado real verificado en el contenedor
productivo (`liquidacion-prestadores-backend-1`, snapshot 2026-08-13):

- `ALT005` (Ruta Compartida) está **activa** en producción — genera alertas y
  observaciones reales hoy (75+ alertas, 20 observaciones `RUTA_COMPARTIDA`
  en el histórico). El default `False` del seed legacy y lo que asumía
  `LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §3/§7 quedaron desactualizados
  respecto de lo que la Team Leader efectivamente usa — se prioriza el
  comportamiento real sobre el default del código legacy.
- `ALT007` (Agrupación de Incidentes) también está activa en producción, pero
  el motor nuevo (`domain/services/motor_reglas/motor.py::CODIGOS_CON_EVALUADOR`)
  no tiene evaluador para ese código, igual que en el legacy. Queda sembrada
  como `True` por fidelidad con producción; no genera ninguna alerta porque
  no hay evaluador que la ejecute — no es un bug, es el mismo comportamiento
  inerte que ya tenía en el sistema viejo.
- `ALT006` (Segunda Visita) es la única inactiva en ambos lados.
"""

import uuid
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "17663a83c3fd"
down_revision: str | None = "2d3c7ac61eeb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (codigo, nombre, descripcion, activa, riesgo_base, configuracion)
_REGLAS: list[tuple[str, str, str, bool, float, dict[str, Any]]] = [
    (
        "ALT001",
        "Precio Incorrecto",
        "El precio cobrado difiere del tarifario vigente para el período",
        True,
        100.0,
        {},
    ),
    (
        "ALT002",
        "KMs Incorrectos",
        "Los kilómetros cobrados difieren de los KMs pactados en la Tabla KM",
        True,
        100.0,
        {"tolerancia_km": 0.5},
    ),
    (
        "ALT003",
        "Posible Viático Duplicado",
        "Se detectaron KMs cobrados en la misma sucursal dentro de la ventana de días "
        "configurada",
        True,
        80.0,
        {"ventana_dias": 30},
    ),
    (
        "ALT004",
        "Servicio Duplicado",
        "El número de incidente ya fue liquidado en una liquidación anterior del mismo PST",
        True,
        90.0,
        {},
    ),
    (
        "ALT005",
        "Ruta Compartida",
        "Múltiples incidentes en la misma zona el mismo día podrían compartir recorrido",
        True,
        40.0,
        {},
    ),
    (
        "ALT006",
        "Segunda Visita",
        "El equipo recibió un servicio reciente del mismo tipo, posible reincidencia",
        False,
        30.0,
        {"ventana_dias": 30},
    ),
    (
        "ALT007",
        "Agrupación de Incidentes",
        "Múltiples incidentes en la misma zona y día podrían agruparse",
        True,
        40.0,
        {},
    ),
    (
        "ALT008",
        "Tarifario Inexistente",
        "No existe tarifario para el tipo de servicio en el período de la fecha de cierre",
        True,
        100.0,
        {},
    ),
    (
        "ALT009",
        "Par Empresa-Sucursal no encontrado en Tabla KM",
        "No existe entrada en la Tabla KM para esta combinación empresa/sucursal con KMs "
        "cobrados",
        True,
        80.0,
        {},
    ),
]

_regla_alerta = sa.table(
    "reglas_alerta",
    sa.column("id", sa.UUID()),
    sa.column("codigo", sa.String()),
    sa.column("nombre", sa.String()),
    sa.column("descripcion", sa.String()),
    sa.column("activa", sa.Boolean()),
    sa.column("riesgo_base", sa.Float()),
    sa.column("configuracion", JSONB()),
)


def upgrade() -> None:
    bind = op.get_bind()
    rows = [
        {
            "id": uuid.uuid4(),
            "codigo": codigo,
            "nombre": nombre,
            "descripcion": descripcion,
            "activa": activa,
            "riesgo_base": riesgo_base,
            "configuracion": configuracion,
        }
        for codigo, nombre, descripcion, activa, riesgo_base, configuracion in _REGLAS
    ]
    bind.execute(
        pg_insert(_regla_alerta).on_conflict_do_nothing(index_elements=["codigo"]), rows
    )


def downgrade() -> None:
    bind = op.get_bind()
    codigos = [r[0] for r in _REGLAS]
    bind.execute(
        sa.text("DELETE FROM reglas_alerta WHERE codigo = ANY(:codigos)"),
        {"codigos": codigos},
    )
