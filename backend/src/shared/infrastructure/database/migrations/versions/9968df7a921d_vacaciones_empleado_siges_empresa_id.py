"""vacaciones empleado siges empresa id

Revision ID: 9968df7a921d
Revises: 7f603c0b3cd2
Create Date: 2026-08-24 14:58:26.200308

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9968df7a921d"
down_revision: str | None = "7f603c0b3cd2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "vacaciones_empleado", sa.Column("siges_empresa_id", sa.Integer(), nullable=True)
    )
    op.create_unique_constraint(
        "uq_vacaciones_empleado_siges_empresa_id", "vacaciones_empleado", ["siges_empresa_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_vacaciones_empleado_siges_empresa_id", "vacaciones_empleado", type_="unique"
    )
    op.drop_column("vacaciones_empleado", "siges_empresa_id")
