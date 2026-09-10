"""liquidaciones modificaciones prestador

Revision ID: 1c95dedec904
Revises: 5a6231d8e3f5
Create Date: 2026-09-10 00:00:00.000000

Tabla `modificaciones_prestador` — registro histórico de cada campo que el
prestador cambió al reconciliar contra AyC (alta/baja/modificación de un
incidente), con antes/después. Ver ADR-038: no es una `Alerta` (esa la
regenera entera el motor de reglas en cada corrida) sino un evento que ya no
es derivable del estado actual una vez que `update_cobrados`/`delete_by_ids`
lo pisan o lo borran. Sin FK al incidente a propósito: una `baja` tiene que
sobrevivir al borrado del incidente.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = '1c95dedec904'
down_revision: str | None = '5a6231d8e3f5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "modificaciones_prestador",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "liquidacion_id",
            UUID(as_uuid=True),
            sa.ForeignKey("liquidaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("numero_incidente", sa.String(), nullable=False),
        sa.Column("tipo_cambio", sa.String(), nullable=False),
        sa.Column("campo", sa.String(), nullable=True),
        sa.Column("valor_anterior", sa.String(), nullable=True),
        sa.Column("valor_nuevo", sa.String(), nullable=True),
        sa.Column(
            "detectada_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("vista_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_modificaciones_prestador_liquidacion_id",
        "modificaciones_prestador",
        ["liquidacion_id"],
    )
    op.create_index(
        "ix_modificaciones_prestador_no_vistas",
        "modificaciones_prestador",
        ["vista_en"],
        postgresql_where=sa.text("vista_en IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_modificaciones_prestador_no_vistas", table_name="modificaciones_prestador"
    )
    op.drop_index(
        "ix_modificaciones_prestador_liquidacion_id", table_name="modificaciones_prestador"
    )
    op.drop_table("modificaciones_prestador")
