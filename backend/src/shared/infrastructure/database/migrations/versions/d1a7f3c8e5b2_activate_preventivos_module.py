"""activate preventivos module

Revision ID: d1a7f3c8e5b2
Revises: c8d4e2f9a1b6
Create Date: 2026-08-14 19:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d1a7f3c8e5b2"
down_revision: str | None = "c8d4e2f9a1b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table(
    "module",
    sa.column("key", sa.String),
    sa.column("is_enabled", sa.Boolean),
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "preventivos").values(is_enabled=True)
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "preventivos").values(is_enabled=False)
    )
