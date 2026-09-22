"""contadores: función "Calendario: ver todos los operadores"

Revision ID: e5a9c3d7b1f4
Revises: d7b2f4e81c93
Create Date: 2026-09-22

ADR-032. El calendario de contadores mostraba los eventos de todos los
operadores (y el filtro por operador) solo al superadmin; el resto ve los
suyos y los que cubre. Esta función concede esa vista completa sin hacer
superadmin al usuario.

Se concede a `aotero@canaldirecto.com.ar` (pedido de Iván, 2026-09-22). Si la
cuenta no existe en la base, el INSERT no hace nada.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5a9c3d7b1f4"
down_revision: str | None = "d7b2f4e81c93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FEATURE_KEY = "contadores-calendario-todos"
GRANT_EMAILS = ("aotero@canaldirecto.com.ar",)

_GRANT_SQL = """
    INSERT INTO user_feature_grant (user_id, feature_key)
    SELECT id, :feature_key FROM app_user WHERE email IN :emails
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
                "label": "Calendario: ver todos los operadores",
                "description": (
                    "Sin esta función cada usuario ve en el calendario solo sus eventos "
                    "y los que cubre."
                ),
                "sort_order": 70,
            }
        ],
    )
    grant = sa.text(_GRANT_SQL).bindparams(
        sa.bindparam("emails", expanding=True), feature_key=FEATURE_KEY, emails=GRANT_EMAILS
    )
    op.execute(grant)
    op.execute(sa.text(_AUDIT_SQL).bindparams(feature_key=FEATURE_KEY))


def downgrade() -> None:
    # user_feature_grant cae en cascada por la FK a module_feature.
    op.execute(sa.text(_DELETE_SQL).bindparams(feature_key=FEATURE_KEY))
