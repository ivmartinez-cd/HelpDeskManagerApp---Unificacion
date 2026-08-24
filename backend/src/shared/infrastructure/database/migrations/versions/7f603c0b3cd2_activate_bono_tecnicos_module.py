"""activate bono tecnicos module

Revision ID: 7f603c0b3cd2
Revises: d9c7013256be
Create Date: 2026-08-24 13:44:28.487034

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7f603c0b3cd2"
down_revision: str | None = "d9c7013256be"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table(
    "module",
    sa.column("key", sa.String),
    sa.column("is_enabled", sa.Boolean),
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(_module.update().where(_module.c.key == "bono-tecnicos").values(is_enabled=True))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        _module.update().where(_module.c.key == "bono-tecnicos").values(is_enabled=False)
    )
