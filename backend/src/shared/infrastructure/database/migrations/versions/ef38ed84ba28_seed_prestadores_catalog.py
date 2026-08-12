"""seed prestadores catalog

Revision ID: ef38ed84ba28
Revises: eab36976e61a
Create Date: 2026-08-12 18:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "ef38ed84ba28"
down_revision: str | None = "eab36976e61a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Deshabilitado (is_enabled=False) hasta probar el módulo completo end-to-end
# — mismo criterio de dos pasos que contadores/sla. sort_order=18: entre sla
# (15) y liquidaciones (20).
MODULES = [("prestadores", "Prestadores", "/prestadores", "wrench", 18, False)]

# view/create/update/delete ya existen en el catálogo global de acciones
# (seed_catalog); solo se declaran los pares (module_key, action_key).
MODULE_ACTIONS = [
    ("prestadores", "view"),
    ("prestadores", "create"),
    ("prestadores", "update"),
    ("prestadores", "delete"),
]

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
    bind.execute(_module_action.delete().where(_module_action.c.module_key == "prestadores"))
    bind.execute(_module.delete().where(_module.c.key == "prestadores"))
