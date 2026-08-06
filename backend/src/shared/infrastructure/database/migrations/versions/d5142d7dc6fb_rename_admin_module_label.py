"""rename admin module label

Revision ID: d5142d7dc6fb
Revises: 4c741806341e
Create Date: 2026-08-06 15:18:03.950971

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5142d7dc6fb"
down_revision: str | None = "4c741806341e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table("module", sa.column("key", sa.String), sa.column("label", sa.String))


def upgrade() -> None:
    op.execute(_module.update().where(_module.c.key == "admin").values(label="Configuración"))


def downgrade() -> None:
    op.execute(_module.update().where(_module.c.key == "admin").values(label="Administración"))
