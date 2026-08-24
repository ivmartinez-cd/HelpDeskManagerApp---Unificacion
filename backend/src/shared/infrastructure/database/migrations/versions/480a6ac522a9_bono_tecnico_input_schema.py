"""bono tecnico input schema

Revision ID: 480a6ac522a9
Revises: abf234e21dcb
Create Date: 2026-08-24 13:16:06.823311

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "480a6ac522a9"
down_revision: str | None = "abf234e21dcb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bono_tecnico_input",
        sa.Column("id_tecnico", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.Integer(), nullable=False),
        sa.Column("tecnico", sa.String(length=120), nullable=False),
        sa.Column("dias", sa.Integer(), nullable=False),
        sa.Column("tareas_varias", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id_tecnico", "periodo"),
    )


def downgrade() -> None:
    op.drop_table("bono_tecnico_input")
