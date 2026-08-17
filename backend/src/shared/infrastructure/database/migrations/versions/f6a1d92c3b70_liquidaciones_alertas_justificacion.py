"""liquidaciones alertas justificacion

Revision ID: f6a1d92c3b70
Revises: e4f8b3c9a2d1
Create Date: 2026-08-17

La TL ahora gestiona las alertas ALT001-009 (resolver/descartar con motivo).
`justificacion` guarda ese motivo — obligatorio al descartar, y preservado por
el re-análisis junto con el estado (ver `conciliar_alertas`).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a1d92c3b70"
down_revision: str | None = "e4f8b3c9a2d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("alertas", sa.Column("justificacion", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("alertas", "justificacion")
