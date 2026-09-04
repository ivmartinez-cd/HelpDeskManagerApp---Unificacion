"""liquidaciones factura pdf url

Revision ID: f2a9c4e8b1d6
Revises: d4f6a8b2c0e1
Create Date: 2026-09-04

URL real del PDF de factura que carga el prestador en AyC (botón "Visualizar" en la
sección FACTURA de webagentes), reconstruida a partir de `Fecha`/`RsPrestador` de
`getLiquidationById` + `numero_factura`/`numero_liquidacion` ya sincronizados —
mismo origen y misma reconciliación que `numero_factura` (P4, sin carga manual).
Nullable: liquidaciones sin factura cargada todavía, o sin los campos necesarios
para reconstruir el nombre de archivo.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2a9c4e8b1d6"
down_revision: str | None = "d4f6a8b2c0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("liquidaciones", sa.Column("factura_pdf_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("liquidaciones", "factura_pdf_url")
