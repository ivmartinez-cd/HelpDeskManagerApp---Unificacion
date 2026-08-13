"""activate liquidaciones module

Revision ID: a000363bd8cd
Revises: 17663a83c3fd
Create Date: 2026-08-13 08:58:12.719329

Habilita `liquidaciones` (sembrado como `is_enabled=False` en
`4c741806341e_seed_catalog.py`, mismo criterio de dos pasos que
insumos/contadores/prestadores/sla) recién después de cargar los datos
reales de producción y verificarlos — ver
`backend/scripts/migrate_liquidaciones_data_from_sqlite.py` y
`LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a000363bd8cd"
down_revision: str | None = "17663a83c3fd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table(
    "module",
    sa.column("key", sa.String),
    sa.column("is_enabled", sa.Boolean),
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(_module.update().where(_module.c.key == "liquidaciones").values(is_enabled=True))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "liquidaciones").values(is_enabled=False)
    )
