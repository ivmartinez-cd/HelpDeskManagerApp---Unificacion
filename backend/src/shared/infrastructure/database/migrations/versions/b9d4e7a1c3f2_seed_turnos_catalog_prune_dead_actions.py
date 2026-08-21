"""seed turnos catalog, prune dead catalog rows

Revision ID: b9d4e7a1c3f2
Revises: a1f3c7e9b2d4
Create Date: 2026-08-21 16:00:00.000000

ADR-029. Tres cosas, todas sobre el catálogo de permisos (ADR-005):

1. Alta del módulo `turnos` (`view`, `manage`). Habilitado desde el arranque:
   backend y pantalla ya están en uso bajo `admin.manage`.
2. Backfill: quien hoy tiene `admin.manage` recibe `turnos.view` + `turnos.manage`
   para no perder acceso a la grilla al cambiar el permiso de los routers. Queda
   auditado como `grant` sin actor (acción de migración, no de un admin).
3. Poda de filas que ningún código chequea y que la grilla de admin mostraba como
   tildeables: `insumos.export`, `analisis-log-hp.export`, `vacaciones.update` y el
   módulo `stc` entero (sin una línea de backend; se vuelve a sembrar cuando exista).
   Los grants que colgaban de esas filas quedan auditados como `revoke`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "b9d4e7a1c3f2"
down_revision: str | None = "a1f3c7e9b2d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (key, label, route, icon, sort_order, is_enabled)
MODULES = [("turnos", "Turnos", "/turnos", "clock", 35, True)]
MODULE_ACTIONS = [("turnos", "view"), ("turnos", "manage")]

PRUNED_MODULE_ACTIONS = [
    ("insumos", "export"),
    ("analisis-log-hp", "export"),
    ("vacaciones", "update"),
    ("stc", "view"),
    ("stc", "export"),
]
PRUNED_MODULES = [("stc", "STC", "/stc", "activity", 50, False)]

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

_BACKFILL_TURNOS_FROM_ADMIN = sa.text(
    """
    WITH ins AS (
        INSERT INTO permission_grant (user_id, module_key, action_key, granted_by)
        SELECT g.user_id, 'turnos', a.action_key, g.granted_by
        FROM permission_grant g
        CROSS JOIN (VALUES ('view'), ('manage')) AS a(action_key)
        WHERE g.module_key = 'admin' AND g.action_key = 'manage'
        ON CONFLICT DO NOTHING
        RETURNING user_id, module_key, action_key
    )
    INSERT INTO permission_audit (actor_user_id, target_user_id, module_key, action_key, operation)
    SELECT NULL, user_id, module_key, action_key, 'grant' FROM ins
    """
)

_REVOKE_PRUNED_GRANTS = sa.text(
    """
    WITH del AS (
        DELETE FROM permission_grant
        WHERE (module_key, action_key) IN (
            ('insumos', 'export'), ('analisis-log-hp', 'export'), ('vacaciones', 'update'),
            ('stc', 'view'), ('stc', 'export')
        )
        RETURNING user_id, module_key, action_key
    )
    INSERT INTO permission_audit (actor_user_id, target_user_id, module_key, action_key, operation)
    SELECT NULL, user_id, module_key, action_key, 'revoke' FROM del
    """
)


def _rows(modules: list[tuple[str, str, str, str, int, bool]]) -> list[dict[str, object]]:
    return [
        {"key": k, "label": lb, "route": r, "icon": i, "sort_order": s, "is_enabled": e}
        for k, lb, r, i, s, e in modules
    ]


def _pairs(pairs: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"module_key": m, "action_key": a} for m, a in pairs]


def _seed(modules: list[dict[str, object]], pairs: list[dict[str, str]]) -> None:
    bind = op.get_bind()
    bind.execute(pg_insert(_module).on_conflict_do_nothing(index_elements=["key"]), modules)
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        pairs,
    )


def upgrade() -> None:
    bind = op.get_bind()
    _seed(_rows(MODULES), _pairs(MODULE_ACTIONS))
    bind.execute(_BACKFILL_TURNOS_FROM_ADMIN)
    bind.execute(_REVOKE_PRUNED_GRANTS)
    for module_key, action_key in PRUNED_MODULE_ACTIONS:
        bind.execute(
            _module_action.delete().where(
                _module_action.c.module_key == module_key,
                _module_action.c.action_key == action_key,
            )
        )
    for key, *_ in PRUNED_MODULES:
        bind.execute(_module.delete().where(_module.c.key == key))


def downgrade() -> None:
    # Los grants de turnos (backfilleados o dados a mano) se pierden con el módulo:
    # no hay forma de distinguirlos y el permiso equivalente vuelve a ser admin.manage.
    bind = op.get_bind()
    _seed(_rows(PRUNED_MODULES), _pairs(PRUNED_MODULE_ACTIONS))
    bind.execute(_module_action.delete().where(_module_action.c.module_key == "turnos"))
    bind.execute(_module.delete().where(_module.c.key == "turnos"))
