"""liquidaciones: tabla acuerdos_precio_cliente

Revision ID: b7d1e9a3c5f2
Revises: a9c4e2f7b1d3
Create Date: 2026-09-05

Acuerdo de precio por cliente dentro de un prestador (factor sobre el tarifario
o precio fijo, con motivo y vigencia) — ver
`domain/entities/acuerdo_precio_cliente.py`. El motor (ALT001) lo toma como el
precio esperado, así la TL deja de resolver a mano cada mes las mismas alertas
con el mismo motivo (caso SALTA: mineras al doble, Refinor y YAGUAR con precio
propio).
"""

import sqlalchemy as sa
from alembic import op

revision = "b7d1e9a3c5f2"
down_revision = "a9c4e2f7b1d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "acuerdos_precio_cliente",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("empresa_nombre", sa.String(), nullable=False),
        sa.Column("tipo_servicio", sa.String(), nullable=True),
        sa.Column("factor", sa.Float(), nullable=True),
        sa.Column("precio_fijo", sa.Float(), nullable=True),
        sa.Column("motivo", sa.String(), nullable=False),
        sa.Column("vigencia_desde", sa.Date(), nullable=False),
        sa.Column("vigencia_hasta", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestadores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_acuerdos_precio_cliente_prestador", "acuerdos_precio_cliente", ["prestador_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_acuerdos_precio_cliente_prestador", table_name="acuerdos_precio_cliente")
    op.drop_table("acuerdos_precio_cliente")
