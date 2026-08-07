"""seed contadores catalog

Revision ID: 5c08ab6175a0
Revises: fc502aa52749
Create Date: 2026-08-07 10:29:45.437839

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "5c08ab6175a0"
down_revision: str | None = "fc502aa52749"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# El diagnóstico original de INTEGRACION_APPS_PLAN.md no incluía a Contadores
# (vive dentro del padre HelpDeskManager-Web, no es una de las 5 apps externas
# auditadas) — corregido 2026-08-07. Confirmado primero en el orden de
# migración de Fase 0. Sigue deshabilitado (is_enabled=False) hasta que el
# módulo completo (las 8 herramientas + UI) esté migrado.
MODULES = [("contadores", "Contadores", "/contadores", "printer", 5, False)]

# "view"/"export" ya existen en el catálogo de acciones (seed_catalog) — no
# hace falta declarar acciones nuevas, solo el par (module_key, action_key).
MODULE_ACTIONS = [("contadores", "view"), ("contadores", "export")]

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
    bind.execute(_module_action.delete().where(_module_action.c.module_key == "contadores"))
    bind.execute(_module.delete().where(_module.c.key == "contadores"))
