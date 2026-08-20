"""dedup turno_asignacion abiertas + índice único parcial (slot_id, user_id)

Revision ID: a1c9f4e7b358
Revises: d4a8c2e6f931
Create Date: 2026-08-19 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1c9f4e7b358"
down_revision: str | None = "d4a8c2e6f931"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DELETE_DUPLICADAS = """
DELETE FROM turno_asignacion t
USING turno_asignacion older
WHERE t.vigente_hasta IS NULL
  AND older.vigente_hasta IS NULL
  AND t.slot_id = older.slot_id
  AND t.user_id = older.user_id
  AND t.id <> older.id
  AND t.id > older.id
"""


def upgrade() -> None:
    # Un mismo operador no puede quedar dos veces con asignación abierta en la
    # misma franja -- limpia primero los duplicados que ya existan (son filas
    # idénticas en slot_id/user_id/vigente_desde, sin señal real de "cuál es más
    # vieja"; se conserva una de forma determinística por id) para que el índice
    # pueda crearse.
    op.execute(_DELETE_DUPLICADAS)
    op.create_index(
        "ux_turno_asignacion_slot_user_abierta",
        "turno_asignacion",
        ["slot_id", "user_id"],
        unique=True,
        postgresql_where="vigente_hasta IS NULL",
    )


def downgrade() -> None:
    op.drop_index("ux_turno_asignacion_slot_user_abierta", table_name="turno_asignacion")
