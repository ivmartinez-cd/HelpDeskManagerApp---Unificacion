"""contadores: función "Proyección: operar candidatos"

Revision ID: 356a35c5112a
Revises: d4c8a1f6e3b7
Create Date: 2026-09-07

ADR-032. El panel de candidatos de Proyección (elegir P/L, forzar método,
aceptar, marcar pendiente, nota) exigía `contadores.manage` completo, que
también da recesos y export — no había forma de conceder solo esa pantalla.
Pasa a aceptar además esta función granular (`require_feature_or_permission`,
ver `proyeccion_candidatos_router.py`); `contadores.manage` sigue alcanzando
por sí solo, no se le saca nada a quien ya lo tiene.

Backfill: se concede a quien ya tiene `contadores.manage`, para que la casilla
quede tildada en la grilla reflejando lo que ese usuario ya podía hacer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "356a35c5112a"
down_revision: str | None = "d4c8a1f6e3b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FEATURE_KEY = "contadores-proyeccion-operar"

_GRANT_SQL = """
    INSERT INTO user_feature_grant (user_id, feature_key)
    SELECT DISTINCT user_id, :feature_key
    FROM (
        SELECT user_id FROM permission_grant
        WHERE module_key = 'contadores' AND action_key = 'manage'
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
                "module_key": "contadores",
                "label": "Proyección: operar candidatos",
                "description": (
                    "Elegir contador P/L, forzar método, aceptar, marcar pendiente y "
                    "nota en el panel de candidatos del Estimador."
                ),
                "sort_order": 60,
            }
        ],
    )
    op.execute(sa.text(_GRANT_SQL).bindparams(feature_key=FEATURE_KEY))
    op.execute(sa.text(_AUDIT_SQL).bindparams(feature_key=FEATURE_KEY))


def downgrade() -> None:
    # user_feature_grant cae en cascada por la FK a module_feature.
    op.execute(sa.text(_DELETE_SQL).bindparams(feature_key=FEATURE_KEY))
