"""seed liquidaciones alt012 serie mismo dia

Revision ID: 97bda6e5991a
Revises: 356a35c5112a
Create Date: 2026-09-08

Nueva regla `ALT012` — Serie Repetida Mismo Día: la misma serie (`nro_serie`)
aparece en dos o más incidentes distintos con la misma `fecha_cierre`, sin
importar el tipo de servicio. Complementa a `ALT010` (que exige tipo opuesto y
solo compara mes/año) — nace de un caso real (Iván, 2026-09-08): dos incidentes
"preventivo" distintos, misma serie, misma sucursal y misma fecha de cierre, sin
ninguna alerta disparada. Ver evaluador en
`domain/services/motor_reglas/alt012_serie_mismo_dia.py`. `riesgo_base=90.0` por
consistencia con `ALT004`/`ALT010` (mismo nivel de riesgo para "duplicado").
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "97bda6e5991a"
down_revision: str | None = "356a35c5112a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

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
    bind.execute(
        pg_insert(_regla_alerta).on_conflict_do_nothing(index_elements=["codigo"]),
        [
            {
                "id": uuid.uuid4(),
                "codigo": "ALT012",
                "nombre": "Serie Repetida Mismo Día",
                "descripcion": (
                    "La serie aparece en dos o más incidentes distintos con la misma "
                    "fecha de cierre, sin importar el tipo de servicio"
                ),
                "activa": True,
                "riesgo_base": 90.0,
                "configuracion": {},
            }
        ],
    )


def downgrade() -> None:
    op.get_bind().execute(sa.text("DELETE FROM reglas_alerta WHERE codigo = 'ALT012'"))
