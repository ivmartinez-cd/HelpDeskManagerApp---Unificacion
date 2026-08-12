"""activate prestadores module

Revision ID: c3a3d55ba3e3
Revises: ef38ed84ba28
Create Date: 2026-08-12 20:00:00.000000

Probado end-to-end contra datos reales (21 PST, sync desde Siges, alta/edición
de PST y contactos, reasignación de operador con historial, filtro de SLA por
operador) antes de habilitarlo.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3a3d55ba3e3"
down_revision: str | None = "ef38ed84ba28"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE module SET is_enabled = true WHERE key = 'prestadores'")


def downgrade() -> None:
    op.execute("UPDATE module SET is_enabled = false WHERE key = 'prestadores'")
