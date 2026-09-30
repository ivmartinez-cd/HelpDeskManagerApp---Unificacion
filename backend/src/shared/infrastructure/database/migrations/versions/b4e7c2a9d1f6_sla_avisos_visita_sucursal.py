"""sla avisos visita en sucursal

Revision ID: b4e7c2a9d1f6
Revises: a8d3f5c1e7b9
Create Date: 2026-09-30 12:00:00.000000

Registro de pares (caso de Mesa de Ayuda, visita de técnico en la misma
sucursal) ya avisados por mail, para no repetir el aviso en cada ciclo del job.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b4e7c2a9d1f6"
down_revision: str | None = "a8d3f5c1e7b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sla_avisos_visita_sucursal",
        sa.Column("id_incidente_mda", sa.Integer(), primary_key=True),
        sa.Column("id_incidente_visita", sa.Integer(), primary_key=True),
        sa.Column(
            "enviado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("sla_avisos_visita_sucursal")
