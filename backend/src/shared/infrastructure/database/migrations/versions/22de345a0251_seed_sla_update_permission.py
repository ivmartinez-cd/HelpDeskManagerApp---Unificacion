"""seed sla update permission

Revision ID: 22de345a0251
Revises: 4c8989f23439
Create Date: 2026-08-12 15:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "22de345a0251"
down_revision: str | None = "4c8989f23439"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# "update" ya existe en el catálogo de acciones (seed_catalog); habilita el
# botón "Actualizar" que fuerza un refresh en vivo contra MERCURIO.
MODULE_ACTIONS = [("sla", "update")]

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
            (_module_action.c.module_key == "sla") & (_module_action.c.action_key == "update")
        )
    )
