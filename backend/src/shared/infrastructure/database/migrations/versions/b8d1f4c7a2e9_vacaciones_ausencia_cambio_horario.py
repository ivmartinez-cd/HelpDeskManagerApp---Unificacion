"""vacaciones: tipo CAMBIO_HORARIO con rango horario en ausencias

Revision ID: b8d1f4c7a2e9
Revises: a7c3e9f1d2b5
Create Date: 2026-08-21 20:30:00.000000

Solicitudes de home office y cambio de horario (decisión del usuario
2026-08-21): se modelan como `vacaciones_ausencia` que el empleado pide
PENDING y la TL aprueba. Esta migración agrega el tipo CAMBIO_HORARIO y las
columnas `hora_desde`/`hora_hasta` (obligatorias solo para ese tipo).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8d1f4c7a2e9"
down_revision: str | None = "a7c3e9f1d2b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLA = "vacaciones_ausencia"
_TIPOS_NUEVOS = (
    "'DESCUENTO_DIA', 'BAJA_ENFERMEDAD', 'TRAMITE_PERSONAL', 'GUARDIA', "
    "'DIA_ESTUDIO', 'HOME_OFFICE', 'CAMBIO_HORARIO', 'OTHER'"
)
_TIPOS_VIEJOS = (
    "'DESCUENTO_DIA', 'BAJA_ENFERMEDAD', 'TRAMITE_PERSONAL', 'GUARDIA', "
    "'DIA_ESTUDIO', 'HOME_OFFICE', 'OTHER'"
)
_HORARIO = (
    "(tipo = 'CAMBIO_HORARIO' AND hora_desde IS NOT NULL AND hora_hasta IS NOT NULL "
    "AND hora_hasta > hora_desde) OR (tipo <> 'CAMBIO_HORARIO' AND hora_desde IS NULL "
    "AND hora_hasta IS NULL)"
)


def upgrade() -> None:
    op.add_column(_TABLA, sa.Column("hora_desde", sa.Time(), nullable=True))
    op.add_column(_TABLA, sa.Column("hora_hasta", sa.Time(), nullable=True))
    op.drop_constraint("ck_vacaciones_ausencia_tipo", _TABLA, type_="check")
    op.create_check_constraint("ck_vacaciones_ausencia_tipo", _TABLA, f"tipo IN ({_TIPOS_NUEVOS})")
    op.create_check_constraint("ck_vacaciones_ausencia_horario", _TABLA, _HORARIO)


def downgrade() -> None:
    # Las ausencias CAMBIO_HORARIO no existen en el modelo anterior: se borran.
    op.execute(f"DELETE FROM {_TABLA} WHERE tipo = 'CAMBIO_HORARIO'")
    op.drop_constraint("ck_vacaciones_ausencia_horario", _TABLA, type_="check")
    op.drop_constraint("ck_vacaciones_ausencia_tipo", _TABLA, type_="check")
    op.create_check_constraint("ck_vacaciones_ausencia_tipo", _TABLA, f"tipo IN ({_TIPOS_VIEJOS})")
    op.drop_column(_TABLA, "hora_hasta")
    op.drop_column(_TABLA, "hora_desde")
