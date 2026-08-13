"""liquidaciones siges empresa id

Revision ID: c4d8a91f26e3
Revises: 8e4079472123
Create Date: 2026-08-13

Vínculo persistente prestador/SPST de liquidaciones → `dbo.Empresa` de Siges
(ADR-014): habilita el sync de configuración desde SigesReadOnly sin matching
por nombre en runtime. Nullable a propósito — el vínculo se establece a mano
desde la UI, fila sin vincular queda fuera del sync.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4d8a91f26e3"
down_revision: str | None = "8e4079472123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prestadores", sa.Column("siges_empresa_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(
        "uq_prestadores_siges_empresa_id", "prestadores", ["siges_empresa_id"]
    )
    op.add_column("spsts", sa.Column("siges_empresa_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_spsts_siges_empresa_id", "spsts", ["siges_empresa_id"])


def downgrade() -> None:
    op.drop_constraint("uq_spsts_siges_empresa_id", "spsts", type_="unique")
    op.drop_column("spsts", "siges_empresa_id")
    op.drop_constraint("uq_prestadores_siges_empresa_id", "prestadores", type_="unique")
    op.drop_column("prestadores", "siges_empresa_id")
