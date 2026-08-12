"""backfill app user color

Revision ID: 60ee5fdc4225
Revises: 4f7c614dafe3
Create Date: 2026-08-12 16:05:00.000000

"""

import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "60ee5fdc4225"
down_revision: str | None = "4f7c614dafe3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_app_user = sa.table(
    "app_user",
    sa.column("id", sa.UUID),
    sa.column("full_name", sa.String),
    sa.column("color", sa.String),
)
_operador = sa.table(
    "contadores_operadores", sa.column("nombre", sa.String), sa.column("color", sa.String)
)


def _normalize(text: str) -> str:
    """Copia de `_normalize` de sqlalchemy_calendario_repository.py — las
    migraciones se mantienen autocontenidas, no importan código de `src.modules`
    que puede cambiar de forma independiente."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def upgrade() -> None:
    bind = op.get_bind()
    # Tabla contadores_operadores puede no existir todavía si el módulo
    # contadores no se migró en este entorno — no es un prerrequisito real.
    inspector = sa.inspect(bind)
    if "contadores_operadores" not in inspector.get_table_names():
        return

    operadores = bind.execute(sa.select(_operador.c.nombre, _operador.c.color)).fetchall()
    color_by_normalized = {_normalize(nombre): color for nombre, color in operadores if color}

    usuarios = bind.execute(
        sa.select(_app_user.c.id, _app_user.c.full_name).where(_app_user.c.color.is_(None))
    ).fetchall()
    for user_id, full_name in usuarios:
        color = color_by_normalized.get(_normalize(full_name))
        if color:
            bind.execute(_app_user.update().where(_app_user.c.id == user_id).values(color=color))


def downgrade() -> None:
    # Irreversible a propósito: no hay forma de distinguir un color puesto acá
    # de uno editado a mano después por un admin (ver UpdateUser).
    pass
