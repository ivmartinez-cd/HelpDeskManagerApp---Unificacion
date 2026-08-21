"""seed analisis-log-hp manage permission

Agrega la acción `manage` al módulo `analisis-log-hp` en el catálogo de permisos.
La acción `manage` global ya existe en la tabla `action` (sembrada en 4c741806341e);
solo falta el vínculo en `module_action`. Hasta ahora, guardar/editar/borrar análisis,
catalogar códigos de error y subir manuales CPMD estaban protegidos únicamente por
`view` — cualquiera con acceso de lectura podía mutar (hallazgo de la auditoría de
ARCHITECTURE_GUIDE.md §8 del 2026-08-21).

Revision ID: 9535d6d405c7
Revises: c3e5a7b9d1f2
Create Date: 2026-08-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "9535d6d405c7"
down_revision: str | None = "c3e5a7b9d1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module_action = sa.table(
    "module_action", sa.column("module_key", sa.String), sa.column("action_key", sa.String)
)

_MODULE = "analisis-log-hp"
_ACTION = "manage"


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        [{"module_key": _MODULE, "action_key": _ACTION}],
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module_action.delete().where(
            (_module_action.c.module_key == _MODULE)
            & (_module_action.c.action_key == _ACTION)
        )
    )
