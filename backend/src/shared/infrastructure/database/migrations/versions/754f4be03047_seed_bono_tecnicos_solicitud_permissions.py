"""seed bono tecnicos solicitud permissions

Revision ID: 754f4be03047
Revises: bff0f583c042
Create Date: 2026-08-24 15:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "754f4be03047"
down_revision: str | None = "bff0f583c042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# "create"/"approve" ya existen en el catálogo de acciones (seed_catalog);
# habilitan el ciclo de solicitud/aprobación de TV (vínculo Empleado↔Siges,
# mismo criterio que vacaciones.CREATE/APPROVE).
MODULE_ACTIONS = [("bono-tecnicos", "create"), ("bono-tecnicos", "approve")]

_module_action = sa.table(
    "module_action", sa.column("module_key", sa.String), sa.column("action_key", sa.String)
)


def upgrade() -> None:
    bind = op.get_bind()
    rows = [{"module_key": m, "action_key": a} for m, a in MODULE_ACTIONS]
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        rows,
    )


def downgrade() -> None:
    bind = op.get_bind()
    for module_key, action_key in MODULE_ACTIONS:
        bind.execute(
            _module_action.delete().where(
                (_module_action.c.module_key == module_key)
                & (_module_action.c.action_key == action_key)
            )
        )
