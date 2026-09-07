"""vacaciones_ausencia: columna para el nombre del certificado adjunto

Revision ID: d4c8a1f6e3b7
Revises: f4b7d2e9a1c5
Create Date: 2026-09-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4c8a1f6e3b7"
down_revision: str | None = "f4b7d2e9a1c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "vacaciones_ausencia",
        sa.Column("certificado_filename", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("vacaciones_ausencia", "certificado_filename")
