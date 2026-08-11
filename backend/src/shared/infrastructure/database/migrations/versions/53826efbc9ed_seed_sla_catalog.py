"""seed sla catalog

Revision ID: 53826efbc9ed
Revises: f7a93b218401
Create Date: 2026-08-11 19:54:12.611502

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "53826efbc9ed"
down_revision: str | None = "f7a93b218401"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Deshabilitado (is_enabled=False) hasta que el módulo completo (backend +
# card de Inicio + pantalla de detalle) esté probado end-to-end contra
# MERCURIO — mismo criterio de dos pasos que usó contadores.
MODULES = [("sla", "SLA", "/sla", "gauge", 15, False)]

# "view" ya existe en el catálogo de acciones (seed_catalog); solo se declara
# el par (module_key, action_key).
MODULE_ACTIONS = [("sla", "view")]

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
    bind.execute(_module_action.delete().where(_module_action.c.module_key == "sla"))
    bind.execute(_module.delete().where(_module.c.key == "sla"))
