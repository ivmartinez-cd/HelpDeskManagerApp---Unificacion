"""tabla_kms: agregar siges_sucursal_id e id_costo_servicios.

`siges_sucursal_id`: FK lógica (no constraint) al ID de Siges de la sucursal cliente.
  Se persiste desde el preview/apply y desde el sync de datos de Siges.

`id_costo_servicios`: IDCostoServicios de esa sucursal en Siges. Es el identificador
  de zona en Siges: enlaza cada sucursal cliente con su base de despacho y su tarifario.
  Reemplaza el rol de spst.siges_base_sucursal_id en el recálculo por fila.

Revision ID: d3e9f4a2c5b8
Revises: c2d8f3a1b4e9
Create Date: 2026-08-16
"""

import sqlalchemy as sa
from alembic import op

revision = "d3e9f4a2c5b8"
down_revision = "c2d8f3a1b4e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tabla_kms", sa.Column("siges_sucursal_id", sa.Integer(), nullable=True))
    op.add_column("tabla_kms", sa.Column("id_costo_servicios", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("tabla_kms", "id_costo_servicios")
    op.drop_column("tabla_kms", "siges_sucursal_id")
