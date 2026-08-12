"""prestadores schema

Revision ID: a575fe7decd1
Revises: 0468811de473
Create Date: 2026-08-12 18:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a575fe7decd1"
down_revision: str | None = "0468811de473"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prestador",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("siges_empresa_id", sa.Integer(), nullable=False),
        sa.Column("den_comercial", sa.String(length=200), nullable=False),
        sa.Column("razon_social", sa.String(length=200), nullable=True),
        sa.Column("cuit", sa.String(length=20), nullable=True),
        sa.Column("operador_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["operador_id"], ["app_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("siges_empresa_id"),
    )
    op.create_table(
        "prestador_contacto",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("is_principal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestador.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "prestador_asignacion_historial",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("operador_id", sa.UUID(), nullable=True),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestador.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operador_id"], ["app_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("prestador_asignacion_historial")
    op.drop_table("prestador_contacto")
    op.drop_table("prestador")
