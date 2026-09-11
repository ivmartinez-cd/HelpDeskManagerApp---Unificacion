"""alt012 exige mismo tipo

Revision ID: 49127af272b7
Revises: 1c95dedec904
Create Date: 2026-09-11

Corrige la descripción sembrada de `ALT012` (migración `97bda6e5991a`): el
evaluador dejó de disparar "sin importar el tipo de servicio" — ahora exige
mismo tipo, porque el caso de tipo opuesto el mismo día ya lo cubre `ALT010`
con más especificidad y las dos alertas se solapaban (reportado por Iván,
2026-09-11, incidente #844009 / serie ZDBXBJFJ90001ZV). Ver
`domain/services/motor_reglas/_coincidencias.py::_coincidencias_alt012`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "49127af272b7"
down_revision: str | None = "1c95dedec904"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DESCRIPCION_NUEVA = (
    "La serie aparece en dos o más incidentes distintos del mismo tipo con la "
    "misma fecha de cierre"
)
_DESCRIPCION_VIEJA = (
    "La serie aparece en dos o más incidentes distintos con la misma "
    "fecha de cierre, sin importar el tipo de servicio"
)


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE reglas_alerta SET descripcion = :descripcion WHERE codigo = 'ALT012'"),
        {"descripcion": _DESCRIPCION_NUEVA},
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE reglas_alerta SET descripcion = :descripcion WHERE codigo = 'ALT012'"),
        {"descripcion": _DESCRIPCION_VIEJA},
    )
