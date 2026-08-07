"""activate contadores module

Revision ID: 6d910a2b8e39
Revises: 5c08ab6175a0
Create Date: 2026-08-07 12:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6d910a2b8e39"
down_revision: str | None = "5c08ab6175a0"
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
        _module.update().where(_module.c.key == "contadores").values(is_enabled=True)
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "contadores").values(is_enabled=False)
    )
