"""seed liquidaciones alt010 serie duplicada

Revision ID: e7a4c1f6b823
Revises: d7f2a4c9e186
Create Date: 2026-08-20

Nueva regla `ALT010` — Serie Duplicada: la misma serie (`nro_serie`) recibió un
servicio preventivo y uno correctivo en el mismo período (mes/año de
`fecha_cierre`). A diferencia de `ALT004` (que compara `numero_incidente`),
compara serie+tipo de servicio — ver evaluador en
`domain/services/motor_reglas/alt010_serie_duplicada.py`. `riesgo_base=90.0`
por consistencia con `ALT004` (mismo nivel de riesgo para "duplicado").
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "e7a4c1f6b823"
down_revision: str | None = "d7f2a4c9e186"
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
                "codigo": "ALT010",
                "nombre": "Serie Duplicada (Preventivo + Correctivo)",
                "descripcion": (
                    "La serie recibió un servicio preventivo y uno correctivo en el "
                    "mismo período"
                ),
                "activa": True,
                "riesgo_base": 90.0,
                "configuracion": {},
            }
        ],
    )


def downgrade() -> None:
    op.get_bind().execute(sa.text("DELETE FROM reglas_alerta WHERE codigo = 'ALT010'"))
