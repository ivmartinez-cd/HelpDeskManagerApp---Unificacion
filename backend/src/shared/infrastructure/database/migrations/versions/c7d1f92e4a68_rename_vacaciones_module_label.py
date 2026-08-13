"""rename vacaciones module label to Gestión de Personal

Revision ID: c7d1f92e4a68
Revises: b9f2d47c8e11
Create Date: 2026-08-13

El módulo engloba Vacaciones + Asistencias + el ABM de personal, así que
"Vacaciones" como título del menú quedaba corto (decisión del usuario,
2026-08-13; el handoff usaba "Gestión Humana" pero colisionaba con el
subítem del ABM, que pasa a llamarse "Personal" en el frontend). Solo cambia
el `label` visible: la key `vacaciones`, la ruta `/vacaciones`, los permisos
y los paths de API no se tocan.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7d1f92e4a68"
down_revision: str | None = "b9f2d47c8e11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table(
    "module",
    sa.column("key", sa.String),
    sa.column("label", sa.String),
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update()
        .where(_module.c.key == "vacaciones")
        .values(label="Gestión de Personal")
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "vacaciones").values(label="Vacaciones")
    )
