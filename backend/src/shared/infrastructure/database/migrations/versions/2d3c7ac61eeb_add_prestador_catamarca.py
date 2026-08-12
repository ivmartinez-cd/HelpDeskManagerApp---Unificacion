"""add prestador catamarca

Revision ID: 2d3c7ac61eeb
Revises: c3a3d55ba3e3
Create Date: 2026-08-12 21:00:00.000000

Resuelve el gap dejado a propósito en `eab36976e61a_seed_prestadores_data`:
`PST Catamarca - Ramon Orellana` de la planilla no tenía un match inequívoco
en Siges. Verificado ahora contra la base real:

- `ID_Empresa=493` ("NO USAR - PST Catamarca - SEI Computacion" / razón
  social "NO USAR - Orellana Ramon") — el nombre coincide con la planilla,
  pero `Estado=1` (inactivo, mismo patrón que los otros "NO USAR" del
  catálogo) y CERO incidentes recientes de Siges lo referencian como técnico.
- `ID_Empresa=1071` ("PST Catamarca - Click Catamarca SRL") — `Estado=0`
  (activo) y es el que efectivamente aparece en los últimos incidentes de
  Catamarca (mayo-julio 2026). Es el PST real que hoy atiende Catamarca en
  SLA, aunque el nombre no coincida textualmente con la planilla.

Se usa 1071: si el vínculo fuera 493, el filtro de SLA por operador nunca
mostraría nada para este PST porque Siges no le imputa ningún incidente.
El contacto (Sonia / seicomputacion.sonia@gmail.com) se conserva tal cual
viene de la planilla — es el único dato de contacto real disponible; puede
estar desactualizado y conviene confirmarlo con el operador.
"""

import uuid
from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "2d3c7ac61eeb"
down_revision: str | None = "c3a3d55ba3e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SIGES_EMPRESA_ID = 1071
_DESDE_REDISTRIBUCION = date(2026, 8, 12)

_prestador = sa.table(
    "prestador",
    sa.column("id", sa.UUID()),
    sa.column("siges_empresa_id", sa.Integer()),
    sa.column("den_comercial", sa.String()),
    sa.column("razon_social", sa.String()),
    sa.column("cuit", sa.String()),
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
    mjvela_id = bind.execute(
        sa.text("SELECT id FROM app_user WHERE email = 'mjvela@canaldirecto.com.ar'")
    ).scalar_one()

    prestador_id = uuid.uuid4()
    bind.execute(
        _prestador.insert().values(
            id=prestador_id,
            siges_empresa_id=_SIGES_EMPRESA_ID,
            den_comercial="PST Catamarca - Click Catamarca SRL",
            razon_social="CLICK CATAMARCA SRL",
            cuit="30715629522",
            operador_id=mjvela_id,
            is_active=True,
        )
    )
    bind.execute(
        _contacto.insert().values(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            nombre="Sonia",
            telefono="54 9 3834 00-5261",
            email="seicomputacion.sonia@gmail.com",
            is_principal=True,
            sort_order=0,
        )
    )
    bind.execute(
        _historial.insert().values(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            operador_id=mjvela_id,
            desde=_DESDE_REDISTRIBUCION,
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM prestador WHERE siges_empresa_id = :id"),
        {"id": _SIGES_EMPRESA_ID},
    )
