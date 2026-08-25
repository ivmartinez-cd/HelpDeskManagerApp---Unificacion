"""bono tecnico input dias soporta medios dias

Revision ID: 3a3413f691c5
Revises: 754f4be03047
Create Date: 2026-08-25 14:50:06.253975

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "3a3413f691c5"
down_revision: str | None = "754f4be03047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "bono_tecnico_input",
        "dias",
        type_=sa.Numeric(4, 1),
        existing_type=sa.Integer(),
        postgresql_using="dias::numeric(4,1)",
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "bono_tecnico_input",
        "dias",
        type_=sa.Integer(),
        existing_type=sa.Numeric(4, 1),
        postgresql_using="round(dias)::integer",
        nullable=False,
    )
