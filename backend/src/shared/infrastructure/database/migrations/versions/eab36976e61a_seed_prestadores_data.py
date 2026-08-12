"""seed prestadores data

Revision ID: eab36976e61a
Revises: a575fe7decd1
Create Date: 2026-08-12 18:35:00.000000

Carga los PST reales de la planilla de seguimiento operador↔PST (captura del
2026-08-12), con la redistribución de la cartera de mpollero (ya no está en
la empresa) ya aplicada: Caleta Olivia y Catamarca quedaron con mjvela;
Concepción del Uruguay/Mar del Plata/Olavarría/Paraná/Rosario con vipaez;
Río Grande/Viedma con ltorres.

`siges_empresa_id` es el `ID_Empresa` real de Siges (`dbo.Empresa`), cruzado
en vivo contra la base — la planilla nombra al PST por el contacto, Siges por
la denominación comercial, y no coinciden como texto (ver plan). PST Catamarca
- Ramon Orellana queda deliberadamente afuera de este seed: su fila de la
planilla apunta a un registro de Siges marcado "NO USAR", sin un match
inequívoco al PST activo real — se resuelve a mano desde la UI, no se adivina.

`desde` de la primera asignación: 2025-09-04 para las carteras originales
(la fecha del encabezado de la planilla, "Operador desde 04/09/2025"); para
las 9 reasignadas tras la salida de mpollero se usa la fecha de esta
migración como aproximación, porque la fecha real del cambio no está
documentada en ningún lado — si se conoce, corregirla desde el historial en
la UI.
"""

import uuid
from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "eab36976e61a"
down_revision: str | None = "a575fe7decd1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DESDE_ORIGINAL = date(2025, 9, 4)
_DESDE_REDISTRIBUCION = date(2026, 8, 12)

# (siges_empresa_id, den_comercial, operador_email, desde, is_active,
#  [(nombre, telefono, email), ...])
_PRESTADORES: list[tuple[int, str, str | None, date, bool, list[tuple[str, str, str]]]] = [
    (
        137,
        "PST Cordoba - Pentacom S.A.",
        "marodriguez@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Marcelo Maenza", "54 9 3515 32-7214", "sop_al_servicio@pentacom.com.ar")],
    ),
    (
        1303,
        "PST Bahia Blanca - Eduardo Lledos",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Eduardo Lledos", "54 9 2915 77-6320", "bahiablanca@inknara.com.ar")],
    ),
    (
        963,
        "PST Chaco - Asesores Informaticos",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Uriel Gallo - Alberto", "54 9 3794 23-3842", "mesa3@aissrl.com.ar")],
    ),
    (
        1278,
        "PST Chacabuco - Microhard",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Mariano - Mauricio", "54 9 2352 49-5097", "microhardchacabuco@outlook.es")],
    ),
    (
        1080,
        "PST Chivilcoy - Ricser Junin SRL",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [
            ("Silvina", "54 9 2364 50-5991", "chivilcoy@ricser-junin.com.ar"),
            ("Sofia", "54 9 2364 70-1110", "sofia_ricser@yahoo.com"),
        ],
    ),
    (
        1219,
        "PST Comodoro Rivadavia - AEG Soluciones Tecnologicas SRL",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Jorge Dickason", "54 9 2974 36-4939", "soporte.ipg@aeg.com.ar")],
    ),
    (
        1310,
        "PST Junin - Mariano Carlos Amor",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Mariano Amor", "54 9 2364 51-7854", "patriciamolla@carlosamor.com")],
    ),
    (
        787,
        "PST La Rioja - Mario Javier Lopez",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Mario Lopez", "54 9 3804 67-0911", "mjlopez682@gmail.com")],
    ),
    (
        765,
        "PST Reconquista - Alejandro Bogado",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Alejandro Bogado", "54 9 3482 54-2626", "ambsoluciones.ab@gmail.com")],
    ),
    (
        490,
        "PST Salta - InterNet Computacion",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [
            ("Manuel Lajad", "54 9 3876 83-2607", "mlajad@hotmail.com"),
            ("Augusto", "54 9 3875 28-4724", "mlajad@hotmail.com"),
        ],
    ),
    (
        504,
        "PST San Juan - Gestion Integral",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [
            ("David Maldonado", "54 9 2644 14-5930", "davidhugomaldonado@gmail.com"),
            ("Claudia Maldonado", "54 9 2645 47-2960", "gestionintegralsrl@gmail.com"),
            ("Jesus Maldonado", "54 9 2645 09-1913", "gestionintegralsrl@gmail.com"),
        ],
    ),
    (
        1186,
        "PST San Rafael - AG Fotocopiadoras",
        "mjvela@canaldirecto.com.ar",
        _DESDE_ORIGINAL,
        True,
        [("Gaston Perez", "54 9 2604 80-2734", "alfredoperezas@hotmail.com")],
    ),
    (
        764,
        "PST Caleta Olivia - SM Soluciones",
        "mjvela@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("Diego Sosa", "54 9 2974 00-1356", "smsolucionescr@gmail.com")],
    ),
    (
        960,
        "PST Concepción del Uruguay - Javier Argachá",
        "vipaez@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("Javier Argacha", "54 9 3442 48-3449", "argachaj@gmail.com")],
    ),
    (
        876,
        "PST Mar del Plata - Jose Luis Bortolazzi",
        "vipaez@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("Jose Luis Bortolazzi", "54 9 2234 55-6141", "lenovoiramar@hotmail.com")],
    ),
    (
        187,
        "PST Olavarria - Pablo Letier",
        "vipaez@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("Pablo", "54 9 2284 58-2710", "pletier@apexsistemas.com")],
    ),
    (
        302,
        "PST Parana - Macarone Ariel",
        "vipaez@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("Ariel Macarone", "54 9 3434 61-8137", "macarone.ariel@gmail.com")],
    ),
    (
        600,
        "PST Rosario - Supernova Servicios SRL",
        "vipaez@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("German Tasca", "54 9 3415 49-6380", "supernova.adm.snova@gmail.com")],
    ),
    (
        903,
        "PST Rio Grande - Victor Corti",
        "ltorres@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("Victor Corti", "54 9 2964 54-5703", "complexarg@gmail.com")],
    ),
    (
        739,
        "PST Viedma - ElectroMaq",
        "ltorres@canaldirecto.com.ar",
        _DESDE_REDISTRIBUCION,
        True,
        [("Ezequiel Carballo", "54 9 2920 25-6070", "kelocarballo@hotmail.com")],
    ),
    (
        333,
        "PST Esquel - Jorge Ismael Saiff",
        None,
        _DESDE_ORIGINAL,
        False,
        [("Javier", "54 9 2945 33-0777", "online.esquel@gmail.com")],
    ),
]

_prestador = sa.table(
    "prestador",
    sa.column("id", sa.UUID()),
    sa.column("siges_empresa_id", sa.Integer()),
    sa.column("den_comercial", sa.String()),
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
)


def upgrade() -> None:
    bind = op.get_bind()
    operador_ids: dict[str, uuid.UUID] = {
        row[0]: row[1]
        for row in bind.execute(sa.text("SELECT email, id FROM app_user")).fetchall()
    }

    prestador_rows = []
    contacto_rows = []
    historial_rows = []

    for siges_id, den_comercial, operador_email, desde, is_active, contactos in _PRESTADORES:
        prestador_id = uuid.uuid4()
        operador_id = operador_ids.get(operador_email) if operador_email else None
        prestador_rows.append(
            {
                "id": prestador_id,
                "siges_empresa_id": siges_id,
                "den_comercial": den_comercial,
                "operador_id": operador_id,
                "is_active": is_active,
            }
        )
        for i, (nombre, telefono, email) in enumerate(contactos):
            contacto_rows.append(
                {
                    "id": uuid.uuid4(),
                    "prestador_id": prestador_id,
                    "nombre": nombre,
                    "telefono": telefono,
                    "email": email,
                    "is_principal": i == 0,
                    "sort_order": i,
                }
            )
        if operador_id is not None:
            historial_rows.append(
                {
                    "id": uuid.uuid4(),
                    "prestador_id": prestador_id,
                    "operador_id": operador_id,
                    "desde": desde,
                }
            )

    op.bulk_insert(_prestador, prestador_rows)
    op.bulk_insert(_contacto, contacto_rows)
    if historial_rows:
        op.bulk_insert(_historial, historial_rows)


def downgrade() -> None:
    bind = op.get_bind()
    siges_ids = [p[0] for p in _PRESTADORES]
    bind.execute(
        sa.text("DELETE FROM prestador WHERE siges_empresa_id = ANY(:ids)"), {"ids": siges_ids}
    )
