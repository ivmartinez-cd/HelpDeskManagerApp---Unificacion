"""seed bono tecnicos update permission

Revision ID: d9c7013256be
Revises: 480a6ac522a9
Create Date: 2026-08-24 13:16:21.536864

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "d9c7013256be"
down_revision: str | None = "480a6ac522a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# "update" ya existe en el catálogo de acciones (seed_catalog); habilita
# guardar Días/Tareas Varias por técnico y período.
MODULE_ACTIONS = [("bono-tecnicos", "update")]

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
    bind.execute(
        _module_action.delete().where(
            (_module_action.c.module_key == "bono-tecnicos")
            & (_module_action.c.action_key == "update")
        )
    )
