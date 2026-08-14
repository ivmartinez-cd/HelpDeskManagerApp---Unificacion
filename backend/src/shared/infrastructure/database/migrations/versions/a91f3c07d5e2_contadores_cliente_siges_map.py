"""Tabla de alias cliente de Gestión → Empresa de Siges.

El `cliente` de los eventos del calendario de Contadores es texto libre de
Gestión (sin ID); para contar impresoras por cliente hay que cruzarlo contra
`dbo.Empresa` de Siges. El cruce automático (normalizado + contención) cubre
~85%; esta tabla guarda el mapeo manual de los nombres rebeldes (alias,
abreviaturas, anotaciones) y siempre gana sobre el cruce automático.

La PK es compuesta a propósito: un cliente de Gestión puede ser varias
empresas de Siges a la vez ('Salta Refrescos' son 3 regiones,
'Diarco | Potigian | La Gioconda', 'Roemmers / Maprimed') — las impresoras
del cliente son la suma de todas sus filas.

Revision ID: a91f3c07d5e2
Revises: 52c62b06f716
Create Date: 2026-08-14
"""

import sqlalchemy as sa
from alembic import op

revision = "a91f3c07d5e2"
down_revision = "52c62b06f716"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contadores_cliente_siges_map",
        sa.Column("cliente_gestion", sa.String(length=200), primary_key=True),
        sa.Column("siges_empresa_id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("contadores_cliente_siges_map")
