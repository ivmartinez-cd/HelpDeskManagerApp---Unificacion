"""activate sla module

Revision ID: ac5e139e28b4
Revises: 53826efbc9ed
Create Date: 2026-08-11 21:30:39.809334

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ac5e139e28b4"
down_revision: str | None = "53826efbc9ed"
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
        _module.update().where(_module.c.key == "sla").values(is_enabled=True)
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "sla").values(is_enabled=False)
    )
