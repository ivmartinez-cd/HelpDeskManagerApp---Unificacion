"""liquidaciones numero factura

Revision ID: a1f3c7e9b2d4
Revises: c2f8a91d4e73
Create Date: 2026-08-20

Número de factura del prestador (`FacturaLocal`-`FacturaNro` de wsAyC),
sincronizado automáticamente — a diferencia de `concepto_extra`/`monto_extra`
(P4), no tiene carga manual: solo lo escribe la reconciliación contra AyC.
Nullable: liquidaciones sin vínculo AyC, o vinculadas pero aún no facturadas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1f3c7e9b2d4"
down_revision: str | None = "c2f8a91d4e73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("liquidaciones", sa.Column("numero_factura", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("liquidaciones", "numero_factura")
