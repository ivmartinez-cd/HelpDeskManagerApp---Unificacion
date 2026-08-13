"""activate vacaciones module

Revision ID: f4c8d19b3a72
Revises: e8b2a5c91f47
Create Date: 2026-08-13

Habilita `vacaciones` (sembrado como `is_enabled=False` en
`4c741806341e_seed_catalog.py`, mismo criterio de dos pasos que el resto de
los módulos) con la Entrega 1 verificada: backend Gestión Humana + core de
solicitudes/aprobaciones/dashboard y frontend contra el design handoff
`design_handoff_vacaciones/`. La migración de datos reales desde VacaSync
queda documentada en `backend/src/modules/vacaciones/README.md` y corre en
una etapa posterior.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4c8d19b3a72"
down_revision: str | None = "e8b2a5c91f47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table(
    "module",
    sa.column("key", sa.String),
    sa.column("is_enabled", sa.Boolean),
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(_module.update().where(_module.c.key == "vacaciones").values(is_enabled=True))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "vacaciones").values(is_enabled=False)
    )
