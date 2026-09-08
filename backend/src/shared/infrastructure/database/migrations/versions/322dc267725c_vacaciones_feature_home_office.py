"""vacaciones: función "Home office y horario"

Revision ID: 322dc267725c
Revises: 97bda6e5991a
Create Date: 2026-09-08

ADR-032. La pestaña "Home office y horario" de Asistencias (pedir home
office/cambio de horario propio) usaba `vacaciones.create` — el mismo permiso
que "Solicitudes" (pedir vacaciones). No había forma de dar Solicitudes a un
perfil sin darle también Home office (caso: usuario técnico, que solo carga
vacaciones y tareas varias, no home office/cambios de horario).

Pasa a exigir esta función granular o `vacaciones.manage`
(`require_feature_or_permission`, ver `ausencias_router.py`): quien ya tiene
`manage` sigue alcanzando por sí solo, no se le saca nada.

Backfill: se concede a quien ya tiene `vacaciones.create`, para no sacarle a
nadie la función que ya usaba y para que la casilla quede tildada en la
grilla reflejando lo que ese usuario ya podía hacer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "322dc267725c"
down_revision: str | None = "97bda6e5991a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FEATURE_KEY = "vacaciones-home-office"

_GRANT_SQL = """
    INSERT INTO user_feature_grant (user_id, feature_key)
    SELECT DISTINCT user_id, :feature_key
    FROM (
        SELECT user_id FROM permission_grant
        WHERE module_key = 'vacaciones' AND action_key = 'create'
    ) u
    ON CONFLICT DO NOTHING
"""

_AUDIT_SQL = """
    INSERT INTO permission_audit (actor_user_id, target_user_id, module_key, action_key, operation)
    SELECT NULL::uuid, user_id, 'feature', :feature_key, 'grant'
    FROM user_feature_grant WHERE feature_key = :feature_key
"""

_DELETE_SQL = "DELETE FROM module_feature WHERE key = :feature_key"


def upgrade() -> None:
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
            {
                "key": FEATURE_KEY,
                "module_key": "vacaciones",
                "label": "Home office y horario",
                "description": (
                    "Pedir home office o un cambio de horario propio, sin ver el "
                    "registro de asistencias del equipo."
                ),
                "sort_order": 35,
            }
        ],
    )
    op.execute(sa.text(_GRANT_SQL).bindparams(feature_key=FEATURE_KEY))
    op.execute(sa.text(_AUDIT_SQL).bindparams(feature_key=FEATURE_KEY))


def downgrade() -> None:
    # user_feature_grant cae en cascada por la FK a module_feature.
    op.execute(sa.text(_DELETE_SQL).bindparams(feature_key=FEATURE_KEY))
