"""seed tareas varias catalog

Revision ID: 4cb2bcd2b53d
Revises: 322dc267725c
Create Date: 2026-09-08 00:00:00.000000

Separa Tareas Varias (SolicitudTv) del módulo `bono_tecnicos` a su propio
módulo `tareas_varias` (backend + frontend), sin tocar la tabla existente
(`bono_tecnicos_solicitud_tv` sigue siendo el nombre, ver el docstring del
modelo). Este módulo nuevo necesita su propia entrada en el catálogo de
módulos/acciones, y quien ya podía enviar/aprobar TV bajo el permiso viejo
(`bono-tecnicos.create`/`bono-tecnicos.approve`) tiene que seguir pudiendo
hacerlo bajo el nuevo (`tareas-varias.create`/`tareas-varias.approve`) — de
lo contrario alguien pierde acceso solo por el refactor.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "4cb2bcd2b53d"
down_revision: str | None = "322dc267725c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MODULES = [("tareas-varias", "Tareas Varias", "/tareas-varias", "clipboard-list", 17, True)]

# "create"/"approve" ya existen en el catálogo de acciones (seed_catalog),
# mismo criterio que bono-tecnicos (ver 754f4be03047).
MODULE_ACTIONS = [("tareas-varias", "create"), ("tareas-varias", "approve")]

# (módulo/acción viejo -> módulo/acción nuevo) para el backfill de grants.
GRANT_MAP = [
    ("bono-tecnicos", "create", "tareas-varias", "create"),
    ("bono-tecnicos", "approve", "tareas-varias", "approve"),
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
_permission_grant = sa.table(
    "permission_grant",
    sa.column("user_id", sa.String),
    sa.column("module_key", sa.String),
    sa.column("action_key", sa.String),
    sa.column("granted_by", sa.String),
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

    for old_module, old_action, new_module, new_action in GRANT_MAP:
        bind.execute(
            sa.text(
                """
                INSERT INTO permission_grant (user_id, module_key, action_key, granted_by)
                SELECT user_id, :new_module, :new_action, granted_by
                FROM permission_grant
                WHERE module_key = :old_module AND action_key = :old_action
                ON CONFLICT (user_id, module_key, action_key) DO NOTHING
                """
            ),
            {
                "old_module": old_module,
                "old_action": old_action,
                "new_module": new_module,
                "new_action": new_action,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    for _, _, new_module, new_action in GRANT_MAP:
        bind.execute(
            _permission_grant.delete().where(
                (_permission_grant.c.module_key == new_module)
                & (_permission_grant.c.action_key == new_action)
            )
        )
    bind.execute(_module_action.delete().where(_module_action.c.module_key == "tareas-varias"))
    bind.execute(_module.delete().where(_module.c.key == "tareas-varias"))
