"""activar módulo personas

Revision ID: a8d3f5c1e7b9
Revises: f3c9a1d7e2b8
Create Date: 2026-09-28 12:00:00.000000

Fase 3 de la unificación Usuarios + Empleados (ADR-040): el módulo se sembró
apagado en f3c9a1d7e2b8 y se enciende ahora que tiene pantalla. Reemplaza en el
sidebar al ítem Usuarios (módulo admin), que sigue existiendo solo para la
grilla de permisos.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8d3f5c1e7b9"
down_revision: str | None = "f3c9a1d7e2b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table("module", sa.column("key", sa.String), sa.column("is_enabled", sa.Boolean))


def upgrade() -> None:
    op.get_bind().execute(
        _module.update().where(_module.c.key == "personas").values(is_enabled=True)
    )


def downgrade() -> None:
    op.get_bind().execute(
        _module.update().where(_module.c.key == "personas").values(is_enabled=False)
    )
