"""add prestadores cartera ltorres

Revision ID: 9139ff95a2d6
Revises: b241c9c3a464
Create Date: 2026-08-13 13:40:00.000000

Continúa `b241c9c3a464` con el resto de la planilla real de seguimiento
operador↔PST (columnas ocultas de la hoja del usuario, entregadas
2026-08-13): la cartera de **ltorres**. Mismo criterio que la migración
anterior:

- `siges_empresa_id` de los 7 PST nuevos cruzado en vivo contra Siges
  (`dbo.Empresa`), evitando los "NO USAR" que aparecen como decoy para casi
  todos estos nombres (ver `backend/scripts/lookup_siges_empresas.py`).
- Dos PST de esta tanda (Tandil, SM Tucumán) traen "-" en la columna
  "Operador hasta 29/02/2024" — no tuvieron operador anterior identificado,
  así que no se les abre ese tramo (a diferencia del resto, que si lo
  tiene: mpollero/imartinez/amaldonado según corresponda).
- Dos PST de esta tanda (Tandil, SM Tucumán) no traen valor en la columna
  "Equipos" — queda `NULL`, no se inventa un valor.
- Corrige los 2 PST de la cartera de ltorres que ya estaban cargados desde
  `eab36976e61a_seed_prestadores_data` (Río Grande, Viedma): `equipos`, la
  fecha real de redistribución (`desde=2025-08-04`, no la aproximación
  `2026-08-12`), el tramo anterior de mjvela con `hasta=2024-02-29`, y un
  típo de email en el contacto de Viedma que trae corregido la planilla
  nueva ("kelocarballo@hotmail.com" → "kelocarballo@gmail.com").
"""

import uuid
from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "9139ff95a2d6"
down_revision: str | None = "b241c9c3a464"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DESDE_DESCONOCIDA = date(2020, 1, 1)
_HASTA_SALIDA_OPERADOR_ANTERIOR = date(2024, 2, 29)
_DESDE_REDISTRIBUCION_REAL = date(2025, 8, 4)

# (siges_empresa_id, den_comercial, razon_social, cuit, operador_saliente_email | None,
#  equipos | None, (nombre_contacto, telefono, email))
_PRESTADORES_NUEVOS: list[
    tuple[int, str, str, str, str | None, int | None, tuple[str, str, str]]
] = [
    (
        964,
        "PST Formosa - Ricardo Armoa",
        "ARMOA ELVIO RICARDO",
        "20257674615",
        "mpollero@canaldirecto.com.ar",
        41,
        ("Elvio Armoa", "54 9 3704 34-0351", "ricardoarmoa@hotmail.com"),
    ),
    (
        1087,
        "PST Posadas - Patricio Martin Godoy",
        "GODOY PATRICIO MARTIN",
        "20247426265",
        "mpollero@canaldirecto.com.ar",
        110,
        ("Patricio Godoy", "54 9 3764 62-6202", "patriciomgodoy@hotmail.com"),
    ),
    (
        1247,
        "PST Rio Gallegos - Servicio Tecnico Basiglio SA",
        "SERVICO TECNICO BASIGLIO S.A",
        "20078189879",
        "imartinez@canaldirecto.com.ar",
        38,
        ("Leonardo", "54 9 2966 62-5333", "gallegos@luisbasiglio.com.ar"),
    ),
    (
        1102,
        "PST Trelew - Copytec",
        "RADZIVILUK P y ERDOZAIN F",
        "30659360388",
        "mpollero@canaldirecto.com.ar",
        60,
        ("Fernando", "54 9 280 467-4657", "fernando.erdozain@copytec.com.ar"),
    ),
    (
        1272,
        "PST Tandil - Cesar Daniel Basili",
        "BASILI DANIEL CESAR",
        "20163057736",
        None,
        None,
        ("Daniel Basilli", "54 9 2494 55-1613", "daniel.basili@xervice.com.ar"),
    ),
    (
        491,
        "PST Tucuman - NAPA Tucuman",
        "NASELLI GERMAN PABLO",
        "20297151712",
        "amaldonado@canaldirecto.com.ar",
        436,
        ("German Naselli", "54 9 3815 70-6850", "sttucuman@gmail.com"),
    ),
    (
        1285,
        "PST SM de Tucuman - Leonardo Herculano",
        "Leonardo C. Herculano y Jose G. Panico S.H.",
        "33709510369",
        None,
        None,
        ("Leonardo Herculano", "54 9 3816 20-0428", "leonardoherculano1969@gmail.com"),
    ),
]

# (siges_empresa_id, equipos, operador_saliente_email)
_CORRECCIONES_EXISTENTES: list[tuple[int, int, str]] = [
    (903, 31, "mjvela@canaldirecto.com.ar"),  # Rio Grande
    (739, 33, "mjvela@canaldirecto.com.ar"),  # Viedma
]

_VIEDMA_SIGES_ID = 739
_VIEDMA_EMAIL_VIEJO = "kelocarballo@hotmail.com"
_VIEDMA_EMAIL_NUEVO = "kelocarballo@gmail.com"

_prestador = sa.table(
    "prestador",
    sa.column("id", sa.UUID()),
    sa.column("siges_empresa_id", sa.Integer()),
    sa.column("den_comercial", sa.String()),
    sa.column("razon_social", sa.String()),
    sa.column("cuit", sa.String()),
    sa.column("equipos", sa.Integer()),
    sa.column("operador_id", sa.UUID()),
    sa.column("is_active", sa.Boolean()),
)
_contacto = sa.table(
    "prestador_contacto",
    sa.column("id", sa.UUID()),
    sa.column("prestador_id", sa.UUID()),
    sa.column("nombre", sa.String()),
    sa.column("telefono", sa.String()),
    sa.column("email", sa.String()),
    sa.column("is_principal", sa.Boolean()),
    sa.column("sort_order", sa.Integer()),
)
_historial = sa.table(
    "prestador_asignacion_historial",
    sa.column("id", sa.UUID()),
    sa.column("prestador_id", sa.UUID()),
    sa.column("operador_id", sa.UUID()),
    sa.column("desde", sa.Date()),
    sa.column("hasta", sa.Date()),
)


def upgrade() -> None:
    bind = op.get_bind()
    operador_ids: dict[str, uuid.UUID] = {
        row[0]: row[1]
        for row in bind.execute(sa.text("SELECT email, id FROM app_user")).fetchall()
    }
    ltorres_id = operador_ids["ltorres@canaldirecto.com.ar"]

    for siges_id, den_comercial, razon_social, cuit, operador_saliente_email, equipos, (
        nombre,
        telefono,
        email,
    ) in _PRESTADORES_NUEVOS:
        prestador_id = uuid.uuid4()
        bind.execute(
            _prestador.insert().values(
                id=prestador_id,
                siges_empresa_id=siges_id,
                den_comercial=den_comercial,
                razon_social=razon_social,
                cuit=cuit,
                equipos=equipos,
                operador_id=ltorres_id,
                is_active=True,
            )
        )
        bind.execute(
            _contacto.insert().values(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                nombre=nombre,
                telefono=telefono,
                email=email,
                is_principal=True,
                sort_order=0,
            )
        )
        if operador_saliente_email is not None:
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
            _historial.insert().values(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                operador_id=ltorres_id,
                desde=_DESDE_REDISTRIBUCION_REAL,
                hasta=None,
            )
        )

    for siges_id, equipos, operador_saliente_email in _CORRECCIONES_EXISTENTES:
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

    bind.execute(
        sa.text(
            "UPDATE prestador_contacto SET email = :nuevo "
            "WHERE email = :viejo AND prestador_id = ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = :siges_id"
            ")"
        ),
        {
            "nuevo": _VIEDMA_EMAIL_NUEVO,
            "viejo": _VIEDMA_EMAIL_VIEJO,
            "siges_id": _VIEDMA_SIGES_ID,
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
            "viejo": _VIEDMA_EMAIL_VIEJO,
            "nuevo": _VIEDMA_EMAIL_NUEVO,
            "siges_id": _VIEDMA_SIGES_ID,
        },
    )

    siges_ids_existentes = [siges_id for siges_id, _, _ in _CORRECCIONES_EXISTENTES]
    bind.execute(
        sa.text(
            "DELETE FROM prestador_asignacion_historial "
            "WHERE prestador_id IN ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = ANY(:ids)"
            ") AND hasta = :hasta"
        ),
        {"ids": siges_ids_existentes, "hasta": _HASTA_SALIDA_OPERADOR_ANTERIOR},
    )
    bind.execute(
        sa.text(
            "UPDATE prestador_asignacion_historial SET desde = :desde "
            "WHERE prestador_id IN ("
            "  SELECT id FROM prestador WHERE siges_empresa_id = ANY(:ids)"
            ") AND hasta IS NULL"
        ),
        {"desde": date(2026, 8, 12), "ids": siges_ids_existentes},
    )
    bind.execute(
        sa.text("UPDATE prestador SET equipos = NULL WHERE siges_empresa_id = ANY(:ids)"),
        {"ids": siges_ids_existentes},
    )

    siges_ids_nuevos = [siges_id for siges_id, *_ in _PRESTADORES_NUEVOS]
    bind.execute(
        sa.text("DELETE FROM prestador WHERE siges_empresa_id = ANY(:ids)"),
        {"ids": siges_ids_nuevos},
    )
