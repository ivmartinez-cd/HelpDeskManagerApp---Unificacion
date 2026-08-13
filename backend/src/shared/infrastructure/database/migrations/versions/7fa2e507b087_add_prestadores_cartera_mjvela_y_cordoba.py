"""add prestadores cartera mjvela y cordoba

Revision ID: 7fa2e507b087
Revises: 9139ff95a2d6
Create Date: 2026-08-13 14:20:00.000000

Cierra la lectura de la planilla completa (`b241c9c3a464`/`9139ff95a2d6`
cubrieron las carteras de vipaez y ltorres; esta migración cubre el resto:
marodriguez/Córdoba y toda la cartera de mjvela). Todos estos PST ya estaban
cargados desde `eab36976e61a_seed_prestadores_data`/`2d3c7ac61eeb` — acá solo
se agrega `equipos` (no existía) y se completa el tramo del operador
saliente donde corresponde. Decisiones confirmadas por el usuario
(2026-08-13):

- Donde el operador NO cambió (Chacabuco, Junín, Chivilcoy, San Juan) no se
  toca `desde` del tramo vigente — sigue en `2025-09-04`, la fecha real de
  esa asignación, no `2025-08-04` (que solo aplica a los que sí se
  reasignaron). Chacabuco y Junín además no traen valor de `equipos` en la
  planilla — quedan `NULL`.
- Reconquista: HOY (2026-08-13) alguien reasignó manualmente desde la UI
  ese PST a "sin operador" (tramo abierto sin `operador_id`). No se pisa —
  se agrega solo el tramo histórico de amaldonado (anterior a 2024-02-29),
  que no toca el tramo vigente.
- Córdoba/Pentacom: HOY alguien reabrió manualmente un tramo de marodriguez
  (cerró el de `2025-09-04` y abrió uno nuevo `2026-08-12`). Tampoco se
  toca — la planilla no documenta cambio de operador para este PST
  (`hasta`=`desde`=marodriguez), solo se agrega `equipos=760`.
- Chivilcoy: se corrige el email del contacto "Silvina" de
  `chivilcoy@ricser-junin.com.ar` a `chivilcoy@ricser.com.ar` (dominio
  distinto al de Mar del Plata/Viedma, no un typo de una letra — confirmado
  como el correcto por el usuario).
- Catamarca (`siges_empresa_id=1071`) y Caleta Olivia (`764`) sí cambiaron
  de operador según la planilla (amaldonado→mjvela) aunque su `desde`
  actual venía de la aproximación `2026-08-12` de `eab36976e61a` — se
  corrige a `2025-08-04` igual que el resto de los PST reasignados.
"""

import uuid
from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "7fa2e507b087"
down_revision: str | None = "9139ff95a2d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DESDE_DESCONOCIDA = date(2020, 1, 1)
_HASTA_SALIDA_OPERADOR_ANTERIOR = date(2024, 2, 29)
_DESDE_REDISTRIBUCION_REAL = date(2025, 8, 4)

# PST donde el operador SI cambió: se corrige `desde` del tramo vigente y se
# agrega el tramo del operador saliente.
# (siges_empresa_id, equipos, operador_saliente_email)
_RECARTERIZADOS: list[tuple[int, int, str]] = [
    (1303, 221, "amaldonado@canaldirecto.com.ar"),  # Bahia Blanca
    (963, 101, "mpollero@canaldirecto.com.ar"),  # Chaco
    (1219, 49, "mpollero@canaldirecto.com.ar"),  # Comodoro Rivadavia
    (787, 52, "amaldonado@canaldirecto.com.ar"),  # La Rioja
    (490, 265, "amaldonado@canaldirecto.com.ar"),  # Salta
    (1186, 45, "imartinez@canaldirecto.com.ar"),  # San Rafael
    (764, 23, "amaldonado@canaldirecto.com.ar"),  # Caleta Olivia
    (1071, 44, "amaldonado@canaldirecto.com.ar"),  # Catamarca
]

# PST con operador continuo: solo se agrega `equipos`, no se toca el
# historial. (siges_empresa_id, equipos)
_CONTINUOS: list[tuple[int, int]] = [
    (137, 760),  # Cordoba/Pentacom (marodriguez, sin cambio)
    (1080, 169),  # Chivilcoy (mjvela, sin cambio)
    (504, 236),  # San Juan (mjvela, sin cambio)
]

# PST donde el operador cambió pero el tramo vigente NO se toca (reasignado
# manualmente hoy vía la UI, fuera de esta migración): solo se agrega
# `equipos` y el tramo histórico del operador saliente.
# (siges_empresa_id, equipos, operador_saliente_email)
_HISTORIAL_SIN_TOCAR_VIGENTE: list[tuple[int, int, str]] = [
    (765, 17, "amaldonado@canaldirecto.com.ar"),  # Reconquista
]

_CHIVILCOY_SIGES_ID = 1080
_CHIVILCOY_EMAIL_VIEJO = "chivilcoy@ricser-junin.com.ar"
_CHIVILCOY_EMAIL_NUEVO = "chivilcoy@ricser.com.ar"

_historial = sa.table(
    "prestador_asignacion_historial",
    sa.column("id", sa.UUID()),
    sa.column("prestador_id", sa.UUID()),
    sa.column("operador_id", sa.UUID()),
    sa.column("desde", sa.Date()),
    sa.column("hasta", sa.Date()),
)


def _operador_ids(bind: sa.engine.Connection) -> dict[str, uuid.UUID]:
    return {
        row[0]: row[1]
        for row in bind.execute(sa.text("SELECT email, id FROM app_user")).fetchall()
    }


def upgrade() -> None:
    bind = op.get_bind()
    operador_ids = _operador_ids(bind)

    for siges_id, equipos in _CONTINUOS:
        bind.execute(
            sa.text("UPDATE prestador SET equipos = :equipos WHERE siges_empresa_id = :id"),
            {"equipos": equipos, "id": siges_id},
        )

    for siges_id, equipos, operador_saliente_email in _RECARTERIZADOS:
        prestador_id = bind.execute(
            sa.text("SELECT id FROM prestador WHERE siges_empresa_id = :id"), {"id": siges_id}
        ).scalar_one()

        bind.execute(
            sa.text("UPDATE prestador SET equipos = :equipos WHERE id = :id"),
            {"equipos": equipos, "id": prestador_id},
        )
        bind.execute(
            sa.text(
                "UPDATE prestador_asignacion_historial SET desde = :desde "
                "WHERE prestador_id = :prestador_id AND hasta IS NULL"
            ),
            {"desde": _DESDE_REDISTRIBUCION_REAL, "prestador_id": prestador_id},
        )
        bind.execute(
            _historial.insert().values(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                operador_id=operador_ids[operador_saliente_email],
                desde=_DESDE_DESCONOCIDA,
                hasta=_HASTA_SALIDA_OPERADOR_ANTERIOR,
            )
        )

    for siges_id, equipos, operador_saliente_email in _HISTORIAL_SIN_TOCAR_VIGENTE:
        prestador_id = bind.execute(
            sa.text("SELECT id FROM prestador WHERE siges_empresa_id = :id"), {"id": siges_id}
        ).scalar_one()

        bind.execute(
            sa.text("UPDATE prestador SET equipos = :equipos WHERE id = :id"),
            {"equipos": equipos, "id": prestador_id},
        )
        bind.execute(
            _historial.insert().values(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                operador_id=operador_ids[operador_saliente_email],
                desde=_DESDE_DESCONOCIDA,
                hasta=_HASTA_SALIDA_OPERADOR_ANTERIOR,
            )
        )

    bind.execute(
        sa.text(
            "UPDATE prestador_contacto SET email = :nuevo "
            "WHERE email = :viejo AND prestador_id = ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = :siges_id"
            ")"
        ),
        {
            "nuevo": _CHIVILCOY_EMAIL_NUEVO,
            "viejo": _CHIVILCOY_EMAIL_VIEJO,
            "siges_id": _CHIVILCOY_SIGES_ID,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            "UPDATE prestador_contacto SET email = :viejo "
            "WHERE email = :nuevo AND prestador_id = ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = :siges_id"
            ")"
        ),
        {
            "viejo": _CHIVILCOY_EMAIL_VIEJO,
            "nuevo": _CHIVILCOY_EMAIL_NUEVO,
            "siges_id": _CHIVILCOY_SIGES_ID,
        },
    )

    for siges_id, _, _ in _HISTORIAL_SIN_TOCAR_VIGENTE:
        bind.execute(
            sa.text(
                "DELETE FROM prestador_asignacion_historial "
                "WHERE prestador_id = (SELECT id FROM prestador WHERE siges_empresa_id = :id) "
                "AND hasta = :hasta"
            ),
            {"id": siges_id, "hasta": _HASTA_SALIDA_OPERADOR_ANTERIOR},
        )
        bind.execute(
            sa.text("UPDATE prestador SET equipos = NULL WHERE siges_empresa_id = :id"),
            {"id": siges_id},
        )

    recarterizados_ids = [siges_id for siges_id, _, _ in _RECARTERIZADOS]
    bind.execute(
        sa.text(
            "DELETE FROM prestador_asignacion_historial "
            "WHERE prestador_id IN ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = ANY(:ids)"
            ") AND hasta = :hasta"
        ),
        {"ids": recarterizados_ids, "hasta": _HASTA_SALIDA_OPERADOR_ANTERIOR},
    )
    # Restaura el `desde` original de cada uno: `2025-09-04` para todos
    # salvo Caleta Olivia/Catamarca, que venían de la redistribución
    # (`2026-08-12`).
    bind.execute(
        sa.text(
            "UPDATE prestador_asignacion_historial SET desde = :desde "
            "WHERE prestador_id IN ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = ANY(:ids)"
            ") AND hasta IS NULL"
        ),
        {"desde": date(2025, 9, 4), "ids": [i for i in recarterizados_ids if i not in (764, 1071)]},
    )
    bind.execute(
        sa.text(
            "UPDATE prestador_asignacion_historial SET desde = :desde "
            "WHERE prestador_id IN ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = ANY(:ids)"
            ") AND hasta IS NULL"
        ),
        {"desde": date(2026, 8, 12), "ids": [764, 1071]},
    )
    bind.execute(
        sa.text("UPDATE prestador SET equipos = NULL WHERE siges_empresa_id = ANY(:ids)"),
        {"ids": recarterizados_ids},
    )

    continuos_ids = [siges_id for siges_id, _ in _CONTINUOS]
    bind.execute(
        sa.text("UPDATE prestador SET equipos = NULL WHERE siges_empresa_id = ANY(:ids)"),
        {"ids": continuos_ids},
    )
