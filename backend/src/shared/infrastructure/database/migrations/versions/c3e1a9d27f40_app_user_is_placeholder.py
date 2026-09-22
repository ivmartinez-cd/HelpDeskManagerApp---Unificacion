"""app_user is_placeholder

Revision ID: c3e1a9d27f40
Revises: 49127af272b7
Create Date: 2026-09-22

Agrega `app_user.is_placeholder` para distinguir las filas que no son usuarios
reales sino referencias históricas: los ex operadores `mpollero` y `amaldonado`
que creó `b241c9c3a464` solo para no perder su nombre en
`prestador_asignacion_historial`. No se pueden borrar (el historial los
referencia), pero no tienen que aparecer en el ABM de Usuarios (pedido de Iván,
2026-09-22).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3e1a9d27f40"
down_revision: str | None = "49127af272b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PLACEHOLDER_EMAILS = ("mpollero@canaldirecto.com.ar", "amaldonado@canaldirecto.com.ar")


def upgrade() -> None:
    op.add_column(
        "app_user",
        sa.Column("is_placeholder", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.execute(
        sa.text("UPDATE app_user SET is_placeholder = true WHERE email IN :emails").bindparams(
            sa.bindparam("emails", value=_PLACEHOLDER_EMAILS, expanding=True)
        )
    )


def downgrade() -> None:
    op.drop_column("app_user", "is_placeholder")
