"""activate analisis_log_hp module

Revision ID: c2e5f8a3d9b1
Revises: b7e4c9f2d1a3
Create Date: 2026-08-15

Habilita `analisis-log-hp` (sembrado como `is_enabled=False` en el
seed_catalog y renombrado por `b7e4c9f2d1a3`) con el backend completo
verificado: dominio, 13 casos de uso, infraestructura (SDS Portal / Insight /
Anthropic / SQLAlchemy), 4 routers y job de snapshots. Frontend entregado
contra el design handoff `design_handoff_analisis_log_hp/`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c2e5f8a3d9b1"
down_revision: str | None = "b7e4c9f2d1a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table(
    "module",
    sa.column("key", sa.String),
    sa.column("is_enabled", sa.Boolean),
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update()
        .where(_module.c.key == "analisis-log-hp")
        .values(is_enabled=True)
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update()
        .where(_module.c.key == "analisis-log-hp")
        .values(is_enabled=False)
    )
