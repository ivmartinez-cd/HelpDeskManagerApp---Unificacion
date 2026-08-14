"""seed liquidaciones delete permission

Agrega la acción `delete` al módulo `liquidaciones` en el catálogo de permisos.
La acción `delete` global ya existe en la tabla `action` (sembrada en 4c741806341e);
solo falta el vínculo en `module_action`.

Revision ID: 52c62b06f716
Revises: c7d1f92e4a68
Create Date: 2026-08-14 10:59:39.769254

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "52c62b06f716"
down_revision: str | None = "c7d1f92e4a68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module_action = sa.table(
    "module_action", sa.column("module_key", sa.String), sa.column("action_key", sa.String)
)

_MODULE = "liquidaciones"
_ACTION = "delete"


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
