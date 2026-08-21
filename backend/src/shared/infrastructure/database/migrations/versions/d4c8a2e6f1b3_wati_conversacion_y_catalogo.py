"""wati: tabla de conversaciones + módulo en el catálogo de permisos

Revision ID: d4c8a2e6f1b3
Revises: b9d4e7a1c3f2
Create Date: 2026-08-21 17:30:00.000000

1. Tabla `wati_conversacion`: estado derivado por número de WhatsApp (quién
   espera a quién), reescrito en cada sincronización contra la API de WATI.
2. Alta del módulo `wati` (`view`, `update`) en el catálogo (ADR-005),
   habilitado desde el arranque: la card de Inicio y la pantalla /wati son
   solo lectura del estado sincronizado.
3. Backfill: `wati.view` para todo usuario que ya tenga algún permiso (la
   card es para que TODOS los operadores vean los chats sin responder);
   `wati.update` (forzar sincronización) para quienes tienen `admin.manage`.
   Auditado como `grant` sin actor (acción de migración).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "d4c8a2e6f1b3"
down_revision: str | None = "b9d4e7a1c3f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MODULES = [("wati", "WhatsApp", "/wati", "message-circle", 36, True)]
MODULE_ACTIONS = [("wati", "view"), ("wati", "update")]

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

_BACKFILL_VIEW_A_TODOS = sa.text(
    """
    WITH ins AS (
        INSERT INTO permission_grant (user_id, module_key, action_key, granted_by)
        SELECT DISTINCT g.user_id, 'wati', 'view', NULL::uuid
        FROM permission_grant g
        ON CONFLICT DO NOTHING
        RETURNING user_id, module_key, action_key
    )
    INSERT INTO permission_audit (actor_user_id, target_user_id, module_key, action_key, operation)
    SELECT NULL, user_id, module_key, action_key, 'grant' FROM ins
    """
)

_BACKFILL_UPDATE_DESDE_ADMIN = sa.text(
    """
    WITH ins AS (
        INSERT INTO permission_grant (user_id, module_key, action_key, granted_by)
        SELECT g.user_id, 'wati', 'update', g.granted_by
        FROM permission_grant g
        WHERE g.module_key = 'admin' AND g.action_key = 'manage'
        ON CONFLICT DO NOTHING
        RETURNING user_id, module_key, action_key
    )
    INSERT INTO permission_audit (actor_user_id, target_user_id, module_key, action_key, operation)
    SELECT NULL, user_id, module_key, action_key, 'grant' FROM ins
    """
)


def _crear_tabla() -> None:
    op.create_table(
        "wati_conversacion",
        sa.Column("wa_id", sa.String(length=32), primary_key=True),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("ticket_id", sa.String(length=64), nullable=True),
        sa.Column("operador_nombre", sa.String(length=120), nullable=True),
        sa.Column("operador_email", sa.String(length=200), nullable=True),
        sa.Column("ultimo_mensaje_cliente_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("esperando_desde", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultima_respuesta_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_bot_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cerrada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bot_activo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "ultimo_texto_cliente",
            sa.String(length=160),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("sincronizado_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_wati_conversacion_esperando",
        "wati_conversacion",
        ["esperando_desde"],
        postgresql_where=sa.text("esperando_desde IS NOT NULL"),
    )


def _seed_catalogo() -> None:
    bind = op.get_bind()
    module_rows = [
        {"key": k, "label": lb, "route": r, "icon": i, "sort_order": s, "is_enabled": e}
        for k, lb, r, i, s, e in MODULES
    ]
    bind.execute(pg_insert(_module).on_conflict_do_nothing(index_elements=["key"]), module_rows)
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        [{"module_key": m, "action_key": a} for m, a in MODULE_ACTIONS],
    )


def upgrade() -> None:
    _crear_tabla()
    _seed_catalogo()
    bind = op.get_bind()
    bind.execute(_BACKFILL_VIEW_A_TODOS)
    bind.execute(_BACKFILL_UPDATE_DESDE_ADMIN)


def downgrade() -> None:
    # Los grants de wati (backfilleados o dados a mano) se pierden con el módulo.
    bind = op.get_bind()
    bind.execute(_module_action.delete().where(_module_action.c.module_key == "wati"))
    bind.execute(_module.delete().where(_module.c.key == "wati"))
    op.drop_index("ix_wati_conversacion_esperando", table_name="wati_conversacion")
    op.drop_table("wati_conversacion")
