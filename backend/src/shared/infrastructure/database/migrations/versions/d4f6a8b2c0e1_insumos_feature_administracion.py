"""insumos: función "Administración" (Clientes, Configuración, Estadísticas)

Revision ID: d4f6a8b2c0e1
Revises: a1c7e2f4b9d3
Create Date: 2026-09-03

ADR-032. Hasta acá el apartado "Administración" del submenú de Insumos se
abría con `insumos.view`, igual que Solicitudes: cualquier operador podía
tocar clientes, parámetros de operación y estadísticas. Pasa a ser una función
concedible por usuario desde la grilla de permisos.

Backfill: se concede a quien tiene `insumos.delete`, que es la acción que
distingue a un Team leader de un operador en las plantillas (Operador =
view/create/update; Team leader = + delete). Los operadores la pierden a
propósito: es el pedido del usuario (2026-09-03), no un efecto colateral.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4f6a8b2c0e1"
down_revision: str | None = "a1c7e2f4b9d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FEATURE_KEY = "insumos-administracion"

_GRANT_SQL = """
    INSERT INTO user_feature_grant (user_id, feature_key)
    SELECT DISTINCT user_id, :feature_key
    FROM (
        SELECT user_id FROM permission_grant
        WHERE module_key = 'insumos' AND action_key = 'delete'
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
                "module_key": "insumos",
                "label": "Administración",
                "description": "Clientes, configuración y estadísticas del módulo.",
                "sort_order": 10,
            }
        ],
    )
    op.execute(sa.text(_GRANT_SQL).bindparams(feature_key=FEATURE_KEY))
    op.execute(sa.text(_AUDIT_SQL).bindparams(feature_key=FEATURE_KEY))


def downgrade() -> None:
    # user_feature_grant cae en cascada por la FK a module_feature.
    op.execute(sa.text(_DELETE_SQL).bindparams(feature_key=FEATURE_KEY))
