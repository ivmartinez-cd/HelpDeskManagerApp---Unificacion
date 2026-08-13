"""liquidaciones extra item

Revision ID: 2e4b8f9d3a7c
Revises: f4c8d19b3a72
Create Date: 2026-08-13

Campo libre en la liquidación para ítems manuales (seguros, documentación, etc.)
que no provienen de los incidentes importados. Nullable porque las liquidaciones
existentes no tienen el campo; el frontend lo expone como editable desde el
detalle de la liquidación.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2e4b8f9d3a7c"
down_revision: str | None = "f4c8d19b3a72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("liquidaciones", sa.Column("concepto_extra", sa.Text(), nullable=True))
    op.add_column("liquidaciones", sa.Column("monto_extra", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("liquidaciones", "monto_extra")
    op.drop_column("liquidaciones", "concepto_extra")
