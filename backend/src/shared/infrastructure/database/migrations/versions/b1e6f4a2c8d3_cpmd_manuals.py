"""analisis_log_hp: catálogo de manuales CPMD

Revision ID: b1e6f4a2c8d3
Revises: f6a1d92c3b70
Create Date: 2026-08-19 00:00:00.000000

pi_cpmd_manuals — manuales de servicio CPMD (PDF) por familia de modelo HP,
matcheados por keyword contra el nombre del modelo (§botón "Manual CPMD").
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "b1e6f4a2c8d3"
down_revision: str | None = "f6a1d92c3b70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pi_cpmd_manuals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("keywords", ARRAY(sa.Text), nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("pi_cpmd_manuals")
