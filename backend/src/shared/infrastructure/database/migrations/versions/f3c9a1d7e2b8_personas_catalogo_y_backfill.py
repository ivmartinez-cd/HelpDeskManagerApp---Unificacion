"""personas: catálogo de permisos y backfill

Revision ID: f3c9a1d7e2b8
Revises: e5b2d7a9c1f4
Create Date: 2026-09-25 17:00:00.000000

Unificación Usuarios + Empleados (ADR-040, docs/personas/PLAN_UNIFICACION.md).
Siembra el módulo `personas` apagado (`is_enabled=false`): se enciende cuando
exista la pantalla (fase 3), igual que reporte-incidentes. Backfill para que
nadie pierda lo que hoy puede hacer:

- `view` + `update` a quien administra Gestión de Personal o Usuarios
  (vacaciones.manage / admin.manage).
- `manage` (dar y quitar acceso) a quien administra Usuarios (admin.manage).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "f3c9a1d7e2b8"
down_revision: str | None = "e5b2d7a9c1f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MODULE_KEY = "personas"
_ACTIONS = ("view", "update", "manage")

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

_BACKFILL = """
INSERT INTO permission_grant (user_id, module_key, action_key)
SELECT DISTINCT g.user_id, 'personas', :accion
FROM permission_grant g
WHERE (g.module_key, g.action_key) IN ({origenes})
ON CONFLICT DO NOTHING
"""
_ORIGENES_EDICION = "('vacaciones', 'manage'), ('admin', 'manage')"
_ORIGENES_ACCESO = "('admin', 'manage')"


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        pg_insert(_module).on_conflict_do_nothing(index_elements=["key"]),
        [
            {
                "key": _MODULE_KEY,
                "label": "Personas",
                "route": "/personas",
                "icon": "users",
                "sort_order": 1,
                "is_enabled": False,
            }
        ],
    )
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        [{"module_key": _MODULE_KEY, "action_key": a} for a in _ACTIONS],
    )
    for accion in ("view", "update"):
        bind.execute(sa.text(_BACKFILL.format(origenes=_ORIGENES_EDICION)), {"accion": accion})
    bind.execute(sa.text(_BACKFILL.format(origenes=_ORIGENES_ACCESO)), {"accion": "manage"})


def downgrade() -> None:
    # permission_grant cae en cascada al borrar module_action.
    bind = op.get_bind()
    bind.execute(_module_action.delete().where(_module_action.c.module_key == _MODULE_KEY))
    bind.execute(_module.delete().where(_module.c.key == _MODULE_KEY))
