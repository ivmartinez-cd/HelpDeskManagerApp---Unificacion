"""spst: columna siges_base_sucursal_id

Revision ID: b3c9e1f5a2d7
Revises: a4f7b2e9c1d8
Create Date: 2026-08-16

"""

from alembic import op
import sqlalchemy as sa

revision = "b3c9e1f5a2d7"
down_revision = "a4f7b2e9c1d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("spsts", sa.Column("siges_base_sucursal_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("spsts", "siges_base_sucursal_id")
