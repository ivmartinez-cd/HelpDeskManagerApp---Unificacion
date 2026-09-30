"""contadores: clientes FTP vinculados a su grupo económico de Siges

Revision ID: d6b2e8f4a1c7
Revises: c3f8a1d6e9b2
Create Date: 2026-09-30

Usuario y contraseña FTP de cada cliente viven en Siges (`dbo.GrupoEconomico.userftp`
/`passftp`). Un cliente con `grupo_economico_id` los lee de ahí al procesar y no guarda
contraseña propia; los que todavía no se vincularon siguen con la local, que ya no se
puede editar desde la app (auditoría de seguridad 2026-09-30: cambiar el servidor
conservando la contraseña guardada permitía mandarla a un FTP ajeno). El vínculo de los
clientes existentes lo hace `scripts/vincular_ftp_clients_orion.py`, no esta migración:
necesita consultar ORION.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d6b2e8f4a1c7"
down_revision: str | None = "c3f8a1d6e9b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ftp_clients", sa.Column("grupo_economico_id", sa.Integer(), nullable=True))
    op.alter_column("ftp_clients", "password", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Los vinculados quedan sin contraseña local: el downgrade no puede traerla de
    # Siges. Restaurar del backup previo si hace falta procesarlos sin el vínculo.
    op.execute("UPDATE ftp_clients SET password = '' WHERE password IS NULL")
    op.alter_column("ftp_clients", "password", existing_type=sa.String(), nullable=False)
    op.drop_column("ftp_clients", "grupo_economico_id")
