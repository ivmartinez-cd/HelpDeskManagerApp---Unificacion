"""add prestadores pst faltantes y correccion historial vipaez

Revision ID: b241c9c3a464
Revises: f8522ce8b61f
Create Date: 2026-08-13 12:57:57.014346

Carga los 8 PST que faltaban de la planilla real de seguimiento operador↔PST
(captura del 2026-08-13, más completa que la usada en `eab36976e61a`) y
corrige los 5 que ya estaban cargados con esa misma planilla (Concepción del
Uruguay, Mar del Plata, Olavarría, Paraná, Rosario):

- `siges_empresa_id` de los 8 nuevos cruzado en vivo contra Siges
  (`dbo.Empresa`), evitando los registros "NO USAR" que aparecen como
  decoy para varios de estos nombres (ver `backend/scripts/lookup_siges_empresas.py`).
- La planilla trae, por primera vez, la fecha real de la redistribución de
  cartera tras la salida de mpollero: `desde=2025-08-04` (no la aproximación
  `2026-08-12` que se había usado en `eab36976e61a` a falta de un dato mejor).
  Se corrige también en los 5 ya cargados.
- La planilla trae además "Operador hasta 29/02/2024": el tramo anterior de
  cada PST, que nunca se había registrado (columna `hasta` de
  `prestador_asignacion_historial` quedaba siempre NULL). Se agrega ese
  tramo. La fecha de INICIO de ese tramo anterior no está documentada en
  ningún lado — se usa `2020-01-01` como marca de "desde antes de tener
  registro"; corregir manualmente si se conoce la fecha real.
- `mpollero` y `amaldonado` (los operadores salientes) ya no están en la
  empresa y nunca tuvieron usuario en este sistema nuevo. Se crean como
  `app_user` **inactivos** (`is_active=False`, sin acceso real — el login
  los rechaza igual que a cualquier usuario inactivo) solo para poder
  referenciar su nombre en el historial en vez de perderlo como NULL. El
  `full_name` es un placeholder explícito, no un dato verificado — el
  nombre completo real de estas dos personas no está documentado en
  ningún lado de este repo.
- Corrige además un typo de email en el contacto de Mar del Plata
  ("lenovoiramar" → "lenovomiramar") que trae la planilla nueva.
"""

import uuid
from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op
from argon2 import PasswordHasher

revision: str = "b241c9c3a464"
down_revision: str | None = "f8522ce8b61f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DESDE_DESCONOCIDA = date(2020, 1, 1)
_HASTA_SALIDA_MPOLLERO = date(2024, 2, 29)
_DESDE_REDISTRIBUCION_REAL = date(2025, 8, 4)

_PLACEHOLDER_OPERADORES = [
    ("mpollero@canaldirecto.com.ar", "Pollero (ex-operador, placeholder histórico)"),
    ("amaldonado@canaldirecto.com.ar", "Maldonado (ex-operador, placeholder histórico)"),
]

# (siges_empresa_id, den_comercial, razon_social, cuit, operador_saliente_email,
#  equipos, (nombre_contacto, telefono, email))
_PRESTADORES_NUEVOS: list[
    tuple[int, str, str, str, str, int, tuple[str, str, str]]
] = [
    (
        749,
        "PST Corrientes - Gaston Medina",
        "MEDINA GASTON PAULI",
        "20332147863",
        "mpollero@canaldirecto.com.ar",
        210,
        ("Gaston Medina", "54 9 3794 00-1281", "gastonmedina77@gmail.com"),
    ),
    (
        816,
        "PST Jujuy - Alfredo Espinoza",
        "ESPINOZA CESAR CLAUDIO ALFREDO",
        "20285374759",
        "mpollero@canaldirecto.com.ar",
        86,
        ("Alfredo Espinoza", "54 9 3884 07-5361", "alfredosertec@gmail.com"),
    ),
    (
        657,
        "PST Mendoza - System&Print",
        "PIRIZ DIEGO MARTIN",
        "30713400609",
        "mjvela@canaldirecto.com.ar",
        420,
        ("Diego Piriz", "54 9 2615 97-5860", "system.print@hotmail.com"),
    ),
    (
        1249,
        "PST Pergamino - Copiers Fotocopiadoras",
        "VASQUEZ RAUL MIGUEL ANGEL",
        "20085244184",
        "amaldonado@canaldirecto.com.ar",
        78,
        ("Sebastian Vazquez", "54 9 2477 59-3550", "sergio.vazquez@tecval.com.ar"),
    ),
    (
        741,
        "PST San Luis - Angel Paez Cuello",
        "PAEZ CUELLO ANGEL JAVIER",
        "20272698164",
        "imartinez@canaldirecto.com.ar",
        99,
        ("Angel Paez Cuello", "54 9 11 6693-8439", "angeljavierpaez@gmail.com"),
    ),
    (
        154,
        "PST Tres Arroyos - Carlos Douma",
        "DOUMA CARLOS",
        "00137695490",
        "mjvela@canaldirecto.com.ar",
        32,
        ("Carlos Douma", "54 9 2983 64-4673", "carlosdouma@gmail.com"),
    ),
    (
        1066,
        "PST Venado Tuerto - Natali Servicios",
        "Natali Servicios",
        "20177291537",
        "imartinez@canaldirecto.com.ar",
        76,
        ("Claudio Natali", "54 9 3462 66-0704", "ventasnataliservicios@gmail.com"),
    ),
    (
        740,
        "PST Villa Mercedes - Infomac",
        "INFOMAC S. A. S",
        "23269153679",
        "imartinez@canaldirecto.com.ar",
        699,
        ("Mauro", "54 9 11 4162-2069", "Areatecnica@infomac.com.ar"),
    ),
]

# (siges_empresa_id, equipos, operador_saliente_email)
_CORRECCIONES_EXISTENTES: list[tuple[int, int, str]] = [
    (960, 171, "mpollero@canaldirecto.com.ar"),  # Concepción del Uruguay
    (876, 212, "mjvela@canaldirecto.com.ar"),  # Mar del Plata
    (187, 65, "mjvela@canaldirecto.com.ar"),  # Olavarría
    (302, 217, "amaldonado@canaldirecto.com.ar"),  # Paraná
    (600, 641, "mjvela@canaldirecto.com.ar"),  # Rosario
]

_MAR_DEL_PLATA_SIGES_ID = 876
_MAR_DEL_PLATA_EMAIL_VIEJO = "lenovoiramar@hotmail.com"
_MAR_DEL_PLATA_EMAIL_NUEVO = "lenovomiramar@hotmail.com"

_app_user = sa.table(
    "app_user",
    sa.column("id", sa.UUID()),
    sa.column("email", sa.String()),
    sa.column("password_hash", sa.String()),
    sa.column("full_name", sa.String()),
    sa.column("is_active", sa.Boolean()),
)
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


def _crear_operadores_placeholder(bind: sa.engine.Connection) -> None:
    hasher = PasswordHasher()
    for email, full_name in _PLACEHOLDER_OPERADORES:
        existente = bind.execute(
            sa.text("SELECT id FROM app_user WHERE email = :email"), {"email": email}
        ).scalar_one_or_none()
        if existente is not None:
            continue
        bind.execute(
            _app_user.insert().values(
                id=uuid.uuid4(),
                email=email,
                password_hash=hasher.hash(str(uuid.uuid4())),
                full_name=full_name,
                is_active=False,
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    _crear_operadores_placeholder(bind)

    operador_ids: dict[str, uuid.UUID] = {
        row[0]: row[1]
        for row in bind.execute(sa.text("SELECT email, id FROM app_user")).fetchall()
    }
    vipaez_id = operador_ids["vipaez@canaldirecto.com.ar"]

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
                operador_id=vipaez_id,
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
        bind.execute(
            _historial.insert().values(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                operador_id=operador_ids[operador_saliente_email],
                desde=_DESDE_DESCONOCIDA,
                hasta=_HASTA_SALIDA_MPOLLERO,
            )
        )
        bind.execute(
            _historial.insert().values(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                operador_id=vipaez_id,
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
                hasta=_HASTA_SALIDA_MPOLLERO,
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
            "nuevo": _MAR_DEL_PLATA_EMAIL_NUEVO,
            "viejo": _MAR_DEL_PLATA_EMAIL_VIEJO,
            "siges_id": _MAR_DEL_PLATA_SIGES_ID,
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
            "viejo": _MAR_DEL_PLATA_EMAIL_VIEJO,
            "nuevo": _MAR_DEL_PLATA_EMAIL_NUEVO,
            "siges_id": _MAR_DEL_PLATA_SIGES_ID,
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
        {"ids": siges_ids_existentes, "hasta": _HASTA_SALIDA_MPOLLERO},
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

    for email, _ in _PLACEHOLDER_OPERADORES:
        bind.execute(sa.text("DELETE FROM app_user WHERE email = :email"), {"email": email})
