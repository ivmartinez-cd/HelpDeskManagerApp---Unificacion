"""bono tecnico input drop tareas varias

Revision ID: bff0f583c042
Revises: eaddcbd9cd05
Create Date: 2026-08-24 15:05:00.000000

TV dejó de ser un valor cargado a mano por técnico/período: ahora es la
cuenta de `bono_tecnico_solicitud_tv` en estado APROBADA del período (ver
GetPuntajesPeriodo). El dato viejo en esta columna era de prueba/dev, sin
respaldo productivo (módulo `bono_tecnicos` sin commitear todavía).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "bff0f583c042"
down_revision: str | None = "eaddcbd9cd05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("bono_tecnico_input", "tareas_varias")


def downgrade() -> None:
    op.add_column(
        "bono_tecnico_input",
        sa.Column("tareas_varias", sa.Integer(), nullable=False, server_default="0"),
    )
