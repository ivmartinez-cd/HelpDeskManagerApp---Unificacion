"""contadores: fichas de clientes nuevos (onboarding / STC)

Revision ID: a7c3e9f1d2b5
Revises: d4c8a2e6f1b3
Create Date: 2026-08-21 19:30:00.000000

Tabla `contadores_cliente_nuevo`: reemplaza el Excel que la TL de Contadores
llena cuando Comercial manda el mail "Nuevo Negocio | <cliente>" (fecha de
corte, cliente, operador, vendedor, situación) y sigue el armado/envío del
STC una vez que Siges muestra los equipos instalados. Lo que Siges sabe
(instalaciones, contrato vigente, rubro) no se copia: se anota en lectura.
Sin permisos nuevos: usa `contadores.manage`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3e9f1d2b5"
down_revision: str | None = "d4c8a2e6f1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ESTADOS = "'ESPERANDO_INSTALACION', 'STC_PENDIENTE', 'STC_ENVIADO', 'CERRADO'"


def upgrade() -> None:
    op.create_table(
        "contadores_cliente_nuevo",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cliente", sa.String(length=200), nullable=False),
        sa.Column("siges_empresa_id", sa.Integer(), nullable=True),
        sa.Column("contrato_nro", sa.String(length=100), nullable=True),
        sa.Column("fecha_firma", sa.Date(), nullable=True),
        sa.Column("vendedor", sa.String(length=100), nullable=True),
        sa.Column("operador_id", sa.String(length=100), nullable=True),
        sa.Column("implementacion_servicio", sa.String(length=50), nullable=True),
        sa.Column("fecha_estimada_implementacion", sa.Date(), nullable=True),
        sa.Column("fecha_estimada_primera_facturacion", sa.Date(), nullable=True),
        sa.Column("dia_corte", sa.Integer(), nullable=True),
        sa.Column("equipos_previstos", sa.Integer(), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=30),
            server_default="ESPERANDO_INSTALACION",
            nullable=False,
        ),
        sa.Column("stc_enviado_el", sa.Date(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["created_by_user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(f"estado IN ({_ESTADOS})", name="ck_cliente_nuevo_estado"),
        sa.CheckConstraint(
            "dia_corte IS NULL OR (dia_corte BETWEEN 1 AND 31)",
            name="ck_cliente_nuevo_dia_corte",
        ),
    )
    op.create_index("ix_contadores_cliente_nuevo_estado", "contadores_cliente_nuevo", ["estado"])
    op.create_index(
        "ix_contadores_cliente_nuevo_siges_empresa_id",
        "contadores_cliente_nuevo",
        ["siges_empresa_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_contadores_cliente_nuevo_siges_empresa_id", "contadores_cliente_nuevo")
    op.drop_index("ix_contadores_cliente_nuevo_estado", "contadores_cliente_nuevo")
    op.drop_table("contadores_cliente_nuevo")
