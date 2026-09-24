"""contadores_estim_log_nro

Revision ID: b4d8e2a6c913
Revises: 72f9b126f6a9
Create Date: 2026-09-24 18:00:00.000000

Número entero y creciente de cada entrada de la auditoría de la Proyección
(`contadores_estim_log.nro`), para el `#IdLog` de la OBSERVACION del CSV a
SiGes: el Estimador v1.7 escribe el `Id` entero de `Estim_Log`
(`CsvExportService`: `Max(e.Id)` por máquina), no un prefijo del UUID. La PK
sigue siendo el UUID. Las filas existentes reciben su número al agregar la
columna identity.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b4d8e2a6c913"
down_revision: str | None = "72f9b126f6a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLA = "contadores_estim_log"


def upgrade() -> None:
    op.add_column(
        _TABLA,
        sa.Column("nro", sa.BigInteger(), sa.Identity(always=False), nullable=False),
    )
    op.create_unique_constraint("uq_contadores_estim_log_nro", _TABLA, ["nro"])


def downgrade() -> None:
    op.drop_constraint("uq_contadores_estim_log_nro", _TABLA, type_="unique")
    op.drop_column(_TABLA, "nro")
