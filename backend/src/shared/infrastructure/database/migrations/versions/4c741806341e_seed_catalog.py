"""seed catalog

Revision ID: 4c741806341e
Revises: 8bbf8b4979e6
Create Date: 2026-08-06 11:52:11.445543

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "4c741806341e"
down_revision: str | None = "8bbf8b4979e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# El módulo "admin" es el único habilitado desde el día uno; los 5 módulos de
# negocio quedan deshabilitados hasta que cada uno se migre (INTEGRACION_APPS_PLAN.md
# Fase 3/4). (key, label, route, icon, sort_order, is_enabled)
MODULES = [
    ("admin", "Administración", "/admin", "shield", 0, True),
    ("insumos", "Insumos", "/insumos", "package", 10, False),
    ("liquidaciones", "Liquidaciones", "/liquidaciones", "file-text", 20, False),
    ("vacaciones", "Vacaciones", "/vacaciones", "calendar", 30, False),
    ("parque-impresoras", "Parque de Impresoras", "/parque-impresoras", "printer", 40, False),
    ("stc", "STC", "/stc", "activity", 50, False),
]

# (key, label)
ACTIONS = [
    ("view", "Ver"),
    ("create", "Crear"),
    ("update", "Editar"),
    ("delete", "Eliminar"),
    ("approve", "Aprobar"),
    ("export", "Exportar"),
    ("manage", "Administrar"),
]

# (module_key, action_key). Nota: "insumos" deliberadamente no tiene "approve"
# declarado — es el par que se usa para probar la integridad anti-typo de la FK
# compuesta de permission_grant (ver verificación de la Etapa 4).
MODULE_ACTIONS = [
    ("admin", "manage"),
    ("insumos", "view"),
    ("insumos", "create"),
    ("insumos", "update"),
    ("insumos", "delete"),
    ("insumos", "export"),
    ("liquidaciones", "view"),
    ("liquidaciones", "create"),
    ("liquidaciones", "update"),
    ("liquidaciones", "approve"),
    ("liquidaciones", "export"),
    ("vacaciones", "view"),
    ("vacaciones", "create"),
    ("vacaciones", "update"),
    ("vacaciones", "approve"),
    ("parque-impresoras", "view"),
    ("parque-impresoras", "export"),
    ("stc", "view"),
    ("stc", "export"),
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
_action = sa.table("action", sa.column("key", sa.String), sa.column("label", sa.String))
_module_action = sa.table(
    "module_action", sa.column("module_key", sa.String), sa.column("action_key", sa.String)
)


def upgrade() -> None:
    bind = op.get_bind()
    module_rows = [
        {"key": k, "label": lb, "route": r, "icon": i, "sort_order": s, "is_enabled": e}
        for k, lb, r, i, s, e in MODULES
    ]
    action_rows = [{"key": k, "label": lb} for k, lb in ACTIONS]
    module_action_rows = [{"module_key": m, "action_key": a} for m, a in MODULE_ACTIONS]

    bind.execute(pg_insert(_module).on_conflict_do_nothing(index_elements=["key"]), module_rows)
    bind.execute(pg_insert(_action).on_conflict_do_nothing(index_elements=["key"]), action_rows)
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        module_action_rows,
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(_module_action.delete())
    bind.execute(_action.delete())
    bind.execute(_module.delete())
