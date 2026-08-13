"""add prestador cd_prestador_id

Revision ID: d6e3c1b4a829
Revises: 2e4b8f9d3a7c
Create Date: 2026-08-13

Vínculo al `prestador_id` numérico del SOAP wsAyC de Canal Directo. Permite
automatizar el sync de liquidaciones sin depender de la coincidencia de nombres.
UNIQUE para que dos prestadores no apunten al mismo ID de CD.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d6e3c1b4a829"
down_revision: str | None = "2e4b8f9d3a7c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prestadores", sa.Column("cd_prestador_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(
        "uq_prestadores_cd_prestador_id", "prestadores", ["cd_prestador_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_prestadores_cd_prestador_id", "prestadores", type_="unique")
    op.drop_column("prestadores", "cd_prestador_id")
