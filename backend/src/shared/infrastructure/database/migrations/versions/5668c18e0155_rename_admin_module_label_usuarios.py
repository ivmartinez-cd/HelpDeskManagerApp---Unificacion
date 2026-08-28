"""rename admin module label to Usuarios

Revision ID: 5668c18e0155
Revises: 3a3413f691c5
Create Date: 2026-08-28 12:43:33

Tras sacar Turnos del hub de Configuración (ADR-029) y eliminar el hub, el
módulo `admin` tiene una sola pantalla (usuarios y sus permisos); el ítem del
sidebar pasa a llamarse como lo que abre.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5668c18e0155"
down_revision: str | None = "3a3413f691c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_module = sa.table("module", sa.column("key", sa.String), sa.column("label", sa.String))


def upgrade() -> None:
    op.execute(_module.update().where(_module.c.key == "admin").values(label="Usuarios"))


def downgrade() -> None:
    op.execute(_module.update().where(_module.c.key == "admin").values(label="Configuración"))
