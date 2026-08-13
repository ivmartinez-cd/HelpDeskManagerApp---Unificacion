"""add prestador equipos

Revision ID: f8522ce8b61f
Revises: a000363bd8cd
Create Date: 2026-08-13 12:53:15.795729

Cantidad de equipos del parque asignado a cada PST para servicio técnico
(confirmado por el usuario 2026-08-13) — dato de la planilla de seguimiento
operador↔PST que nunca se había modelado (ver `INTEGRACION_APPS_PLAN.md`,
nota de 2026-08-13 sobre los dos módulos "Prestador").
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f8522ce8b61f"
down_revision: str | None = "a000363bd8cd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prestador", sa.Column("equipos", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("prestador", "equipos")
