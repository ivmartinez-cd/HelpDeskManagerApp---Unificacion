"""auth: catálogo de funciones (pantallas/cards) concedibles por usuario

Revision ID: c3e5a7b9d1f2
Revises: b8d1f4c7a2e9
Create Date: 2026-08-21 21:30:00.000000

ADR-032. Hasta acá, qué pantalla/card veía cada usuario salía de reglas en
código sobre módulo × acción (p. ej. "Coberturas requiere manage"). Para que
todo sea editable por usuario desde la UI, esas pantallas pasan a ser
"funciones" del catálogo (`module_feature`) con grants propios
(`user_feature_grant`). Se backfillean según las reglas vigentes hasta hoy,
así nadie ve ni más ni menos que antes hasta que un admin lo edite.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3e5a7b9d1f2"
down_revision: str | None = "b8d1f4c7a2e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (key, module_key, label, description, sort_order)
FEATURES = [
    ("contadores-coberturas", "contadores", "Coberturas",
     "Reemplazos temporales de operadores en el calendario de contadores.", 10),
    ("contadores-anexos", "contadores", "Anexos sin facturar",
     "Listado de anexos pendientes de facturación (Siges).", 20),
    ("contadores-clientes-nuevos", "contadores", "Clientes nuevos",
     "Fichas de clientes nuevos detectados en Siges.", 30),
    ("contadores-sin-real-todos", "contadores", "Sin contador real: ver todos los clientes",
     "Sin esta función solo se ven los equipos de los clientes asignados al usuario.", 40),
    ("contadores-card-operadores", "contadores", "Inicio: card \"Contadores por operador\"",
     "Distribución de clientes e impresoras del mes por operador.", 50),
    ("prestadores-coberturas", "prestadores", "Coberturas",
     "Reemplazos temporales de operadores sobre los PST asignados.", 10),
    ("prestadores-card-parque", "prestadores", "Inicio: card \"Distribución del parque\"",
     "Impresoras por operador.", 20),
    ("vacaciones-dashboard", "vacaciones", "Dashboard del equipo",
     "Resumen y calendario de ausencias de todo el equipo.", 10),
    ("vacaciones-asistencias", "vacaciones", "Registro de asistencias",
     "Bajas y ausencias de todo el equipo.", 20),
    ("vacaciones-gestion-humana", "vacaciones", "Gestión humana",
     "Empleados, sectores, cargos y feriados.", 30),
    ("vacaciones-reportes", "vacaciones", "Reportes", "Reportes de vacaciones (Excel/PDF).", 40),
    ("vacaciones-auditoria", "vacaciones", "Auditoría", "Historial de cambios del módulo.", 50),
    ("vacaciones-configuracion", "vacaciones", "Configuración",
     "Reglas, ciclos y antigüedad del módulo.", 60),
    ("vacaciones-card-equipo", "vacaciones", "Inicio: card \"Próximos días del equipo\"",
     "Vacaciones y home office próximos de todo el equipo.", 70),
]

# Backfill: a quién se le concede cada función según la regla que regía hasta hoy.
# (feature_key, SQL que devuelve user_id)
_MANAGE = "SELECT user_id FROM permission_grant WHERE module_key = '{m}' AND action_key = 'manage'"
_APPROVE_OR_MANAGE = (
    "SELECT user_id FROM permission_grant WHERE module_key = '{m}' "
    "AND action_key IN ('approve', 'manage')"
)
_CREATE_OR_UPDATE = (
    "SELECT user_id FROM permission_grant WHERE module_key = '{m}' "
    "AND action_key IN ('create', 'update')"
)
_UPDATE = "SELECT user_id FROM permission_grant WHERE module_key = '{m}' AND action_key = 'update'"
BACKFILL = [
    ("contadores-coberturas", _MANAGE.format(m="contadores")),
    ("contadores-anexos", _MANAGE.format(m="contadores")),
    ("contadores-clientes-nuevos", _MANAGE.format(m="contadores")),
    ("contadores-sin-real-todos", _MANAGE.format(m="contadores")),
    ("contadores-card-operadores", _MANAGE.format(m="contadores")),
    ("prestadores-coberturas", _CREATE_OR_UPDATE.format(m="prestadores")),
    ("prestadores-card-parque", _UPDATE.format(m="prestadores")),
    ("vacaciones-dashboard", _APPROVE_OR_MANAGE.format(m="vacaciones")),
    ("vacaciones-asistencias", _APPROVE_OR_MANAGE.format(m="vacaciones")),
    ("vacaciones-card-equipo", _APPROVE_OR_MANAGE.format(m="vacaciones")),
    ("vacaciones-gestion-humana", _MANAGE.format(m="vacaciones")),
    ("vacaciones-reportes", _MANAGE.format(m="vacaciones")),
    ("vacaciones-auditoria", _MANAGE.format(m="vacaciones")),
    ("vacaciones-configuracion", _MANAGE.format(m="vacaciones")),
]


def upgrade() -> None:
    op.create_table(
        "module_feature",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column(
            "module_key",
            sa.String(),
            sa.ForeignKey("module.key", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="100"),
        sa.CheckConstraint("key ~ '^[a-z][a-z0-9-]{1,39}$'", name="ck_module_feature_key_format"),
    )
    op.create_table(
        "user_feature_grant",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("app_user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "feature_key",
            sa.String(),
            sa.ForeignKey("module_feature.key", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "granted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("app_user.id", ondelete="SET NULL"),
        ),
    )
    feature = sa.table(
        "module_feature",
        sa.column("key", sa.String),
        sa.column("module_key", sa.String),
        sa.column("label", sa.String),
        sa.column("description", sa.String),
        sa.column("sort_order", sa.SmallInteger),
    )
    op.bulk_insert(
        feature,
        [
            {"key": k, "module_key": m, "label": lb, "description": d, "sort_order": s}
            for k, m, lb, d, s in FEATURES
        ],
    )
    for key, users_sql in BACKFILL:
        op.execute(
            f"INSERT INTO user_feature_grant (user_id, feature_key) "
            f"SELECT DISTINCT user_id, '{key}' FROM ({users_sql}) u ON CONFLICT DO NOTHING"
        )
        op.execute(
            "INSERT INTO permission_audit (actor_user_id, target_user_id, module_key, "
            f"action_key, operation) SELECT NULL::uuid, user_id, 'feature', '{key}', 'grant' "
            f"FROM user_feature_grant WHERE feature_key = '{key}'"
        )


def downgrade() -> None:
    op.drop_table("user_feature_grant")
    op.drop_table("module_feature")
