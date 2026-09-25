"""activar módulo reporte-incidentes

Revision ID: e5b2d7a9c1f4
Revises: d1a4c8e2f6b3
Create Date: 2026-09-25 13:00:00.000000

Segundo paso del alta (mismo criterio que sla): el módulo pasa a verse en el
sidebar ahora que tiene frontend, para probarlo en dev (decisión de Iván,
2026-09-25).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5b2d7a9c1f4"
down_revision: str | None = "d1a4c8e2f6b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table("module", sa.column("key", sa.String), sa.column("is_enabled", sa.Boolean))


def upgrade() -> None:
    op.get_bind().execute(
        _module.update().where(_module.c.key == "reporte-incidentes").values(is_enabled=True)
    )


def downgrade() -> None:
    op.get_bind().execute(
        _module.update().where(_module.c.key == "reporte-incidentes").values(is_enabled=False)
    )
