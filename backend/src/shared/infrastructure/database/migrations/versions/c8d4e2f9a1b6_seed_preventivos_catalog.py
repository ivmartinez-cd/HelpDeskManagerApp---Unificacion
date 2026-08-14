"""seed preventivos catalog

Revision ID: c8d4e2f9a1b6
Revises: b3f1c9a7d2e4
Create Date: 2026-08-14 18:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "c8d4e2f9a1b6"
down_revision: str | None = "b3f1c9a7d2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Deshabilitado (is_enabled=False) hasta que backend + pantalla estén probados
# end-to-end — mismo criterio de dos migraciones que sla/contadores.
# Ícono "calendar-clock" (no "wrench": ya es el de prestadores en el sidebar).
MODULES = [("preventivos", "Preventivos", "/preventivos", "calendar-clock", 45, False)]

# "view" y "update" ya existen en el catálogo de acciones (seed_catalog).
MODULE_ACTIONS = [("preventivos", "view"), ("preventivos", "update")]

_module = sa.table(
    "module",
    sa.column("key", sa.String),
    sa.column("label", sa.String),
    sa.column("route", sa.String),
    sa.column("icon", sa.String),
    sa.column("sort_order", sa.SmallInteger),
    sa.column("is_enabled", sa.Boolean),
)
_module_action = sa.table(
    "module_action", sa.column("module_key", sa.String), sa.column("action_key", sa.String)
)


def upgrade() -> None:
    bind = op.get_bind()
    module_rows = [
        {"key": k, "label": lb, "route": r, "icon": i, "sort_order": s, "is_enabled": e}
        for k, lb, r, i, s, e in MODULES
    ]
    module_action_rows = [{"module_key": m, "action_key": a} for m, a in MODULE_ACTIONS]

    bind.execute(pg_insert(_module).on_conflict_do_nothing(index_elements=["key"]), module_rows)
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        module_action_rows,
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(_module_action.delete().where(_module_action.c.module_key == "preventivos"))
    bind.execute(_module.delete().where(_module.c.key == "preventivos"))
