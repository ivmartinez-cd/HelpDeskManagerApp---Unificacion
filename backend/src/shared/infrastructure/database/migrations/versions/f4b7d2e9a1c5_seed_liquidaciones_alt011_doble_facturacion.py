"""seed liquidaciones alt011 doble facturacion

Revision ID: f4b7d2e9a1c5
Revises: c3e8f1a9d2b4
Create Date: 2026-09-07

Nueva regla `ALT011` — Doble Facturación: el costo de servicio cobrado es
exactamente el doble del esperado (tarifario o acuerdo), en cualquier tipo de
servicio. Separada de `ALT001` para que la TL vea el caso con nombre propio
(doble aprobado por JP a pedido del prestador vs. doble facturación) — ver evaluador en
`domain/services/motor_reglas/alt011_doble_facturacion.py`. `riesgo_base=90.0`
como los duplicados (ALT004/ALT010).
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "f4b7d2e9a1c5"
down_revision: str | None = "c3e8f1a9d2b4"
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
                "codigo": "ALT011",
                "nombre": "Doble Facturación",
                "descripcion": (
                    "El precio cobrado es exactamente el doble del tarifario: "
                    "adicional pedido por el prestador y aprobado por JP, o doble "
                    "facturación"
                ),
                "activa": True,
                "riesgo_base": 90.0,
                "configuracion": {},
            }
        ],
    )


def downgrade() -> None:
    op.get_bind().execute(sa.text("DELETE FROM reglas_alerta WHERE codigo = 'ALT011'"))
