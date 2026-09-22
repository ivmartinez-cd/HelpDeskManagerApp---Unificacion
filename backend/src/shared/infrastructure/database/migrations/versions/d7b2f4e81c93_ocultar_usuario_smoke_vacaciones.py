"""ocultar usuario smoke vacaciones

Revision ID: d7b2f4e81c93
Revises: c3e1a9d27f40
Create Date: 2026-09-22

`smoke.vacaciones@example.com` es una cuenta de prueba (superadmin, creada a
mano, no referenciada en el código). Se desactiva y se marca `is_placeholder`
para sacarla del ABM de Usuarios (pedido de Iván, 2026-09-22). No se borra
porque puede tener filas asociadas (sesiones, auditoría, vacaciones de prueba).
Si la cuenta no existe en la base, el UPDATE no hace nada.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7b2f4e81c93"
down_revision: str | None = "c3e1a9d27f40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMAIL = "smoke.vacaciones@example.com"


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE app_user SET is_active = false, is_placeholder = true WHERE email = :email"
        ).bindparams(email=_EMAIL)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE app_user SET is_active = true, is_placeholder = false WHERE email = :email"
        ).bindparams(email=_EMAIL)
    )
