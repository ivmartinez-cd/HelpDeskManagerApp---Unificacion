"""rename module parque-impresoras to analisis-log-hp

Revision ID: b7e4c9f2d1a3
Revises: a3c8e2f1b9d5
Create Date: 2026-08-15 00:00:00.000000

Actualiza en la base de datos el module_key "parque-impresoras" al nuevo
nombre "analisis-log-hp" — nombre más descriptivo del módulo (análisis de
logs de impresoras HP). Solo afecta a las tablas del catálogo de auth;
las tablas pi_* del módulo no tienen la clave en ningún índice de nombre.

Usa DELETE + INSERT en vez de UPDATE encadenado para evitar la violación
de FK (module_action.module_key → module.key): no es posible renombrar
la clave del padre y del hijo en dos UPDATEs separados sin violar la
constraint en algún punto intermedio, y la FK no es DEFERRABLE.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e4c9f2d1a3"
down_revision: str | None = "a3c8e2f1b9d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_KEY = "parque-impresoras"
_NEW_KEY = "analisis-log-hp"
_NEW_LABEL = "Análisis Logs HP"
_NEW_ROUTE = "/analisis-log-hp"
_OLD_LABEL = "Parque de Impresoras"
_OLD_ROUTE = "/parque-impresoras"

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
    "module_action",
    sa.column("module_key", sa.String),
    sa.column("action_key", sa.String),
)

_ACTIONS = ["view", "export"]


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Leer qué acciones tenía el módulo viejo (para re-insertarlas con el nuevo key)
    rows = bind.execute(
        sa.select(_module_action.c.action_key).where(
            _module_action.c.module_key == _OLD_KEY
        )
    ).fetchall()
    old_actions = [r[0] for r in rows]

    # 2. Leer metadatos actuales del módulo (sort_order, icon, is_enabled)
    mod = bind.execute(
        sa.select(
            _module.c.icon,
            _module.c.sort_order,
            _module.c.is_enabled,
        ).where(_module.c.key == _OLD_KEY)
    ).fetchone()

    # 3. Borrar module_action del key viejo (libera la FK que referencia al módulo)
    bind.execute(
        sa.delete(_module_action).where(_module_action.c.module_key == _OLD_KEY)
    )

    if mod is not None:
        icon, sort_order, is_enabled = mod

        # 4. Borrar módulo viejo
        bind.execute(sa.delete(_module).where(_module.c.key == _OLD_KEY))

        # 5. Insertar módulo con el nuevo key
        bind.execute(
            sa.insert(_module).values(
                key=_NEW_KEY,
                label=_NEW_LABEL,
                route=_NEW_ROUTE,
                icon=icon,
                sort_order=sort_order,
                is_enabled=is_enabled,
            )
        )

    # 6. Re-insertar module_actions con el nuevo key
    if old_actions:
        bind.execute(
            sa.insert(_module_action),
            [{"module_key": _NEW_KEY, "action_key": a} for a in old_actions],
        )


def downgrade() -> None:
    bind = op.get_bind()

    rows = bind.execute(
        sa.select(_module_action.c.action_key).where(
            _module_action.c.module_key == _NEW_KEY
        )
    ).fetchall()
    old_actions = [r[0] for r in rows]

    mod = bind.execute(
        sa.select(_module.c.icon, _module.c.sort_order, _module.c.is_enabled)
        .where(_module.c.key == _NEW_KEY)
    ).fetchone()

    bind.execute(
        sa.delete(_module_action).where(_module_action.c.module_key == _NEW_KEY)
    )

    if mod is not None:
        icon, sort_order, is_enabled = mod
        bind.execute(sa.delete(_module).where(_module.c.key == _NEW_KEY))
        bind.execute(
            sa.insert(_module).values(
                key=_OLD_KEY,
                label=_OLD_LABEL,
                route=_OLD_ROUTE,
                icon=icon,
                sort_order=sort_order,
                is_enabled=is_enabled,
            )
        )

    if old_actions:
        bind.execute(
            sa.insert(_module_action),
            [{"module_key": _OLD_KEY, "action_key": a} for a in old_actions],
        )
