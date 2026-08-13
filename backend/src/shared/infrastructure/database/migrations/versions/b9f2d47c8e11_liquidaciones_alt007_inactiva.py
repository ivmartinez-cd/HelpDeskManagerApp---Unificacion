"""liquidaciones ALT007 inactiva

Revision ID: b9f2d47c8e11
Revises: a7c3f81e42d9
Create Date: 2026-08-13

`ALT007` (Agrupación de Incidentes) se sembró `activa=True` por fidelidad con el
snapshot de producción (`17663a83c3fd`), pero ni el legacy ni el motor nuevo
tienen evaluador para ese código: una regla "activa" que jamás genera nada es
confusión operativa sin ningún efecto funcional (hallazgo H-8 de
`docs/liquidaciones/VALIDACION_PIPELINE_LIQUIDACIONES_2026-08-13.md`). Se
desactiva; si algún día se implementa el evaluador, reactivarla es una decisión
explícita junto con ese código.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b9f2d47c8e11"
down_revision: str | None = "a7c3f81e42d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE reglas_alerta SET activa = false WHERE codigo = 'ALT007'")
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE reglas_alerta SET activa = true WHERE codigo = 'ALT007'")
    )
