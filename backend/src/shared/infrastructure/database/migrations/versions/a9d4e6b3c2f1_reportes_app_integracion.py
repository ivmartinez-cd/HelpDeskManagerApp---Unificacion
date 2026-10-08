"""reportes_app: integración de la rama desde el panel

Revision ID: a9d4e6b3c2f1
Revises: f2c8d4a7e1b9
Create Date: 2026-10-08

`rama`: la que dejó Claude al resolver el reporte. Estados nuevos `integrar`
(el superadmin tocó "Integrar" en el panel) e `integrado` (el script del host
`scripts/integrar_reportes.py` la mergeó a develop).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a9d4e6b3c2f1"
down_revision: str | None = "f2c8d4a7e1b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CK = "ck_reportes_app_estado"
_ESTADOS = "'nuevo', 'propuesto', 'aprobado', 'en_curso', 'resuelto', 'descartado'"


def upgrade() -> None:
    op.add_column("reportes_app", sa.Column("rama", sa.String()))
    op.drop_constraint(_CK, "reportes_app", type_="check")
    op.create_check_constraint(
        _CK, "reportes_app", f"estado IN ({_ESTADOS}, 'integrar', 'integrado')"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE reportes_app SET estado = 'resuelto' WHERE estado IN ('integrar', 'integrado')"
    )
    op.drop_constraint(_CK, "reportes_app", type_="check")
    op.create_check_constraint(_CK, "reportes_app", f"estado IN ({_ESTADOS})")
    op.drop_column("reportes_app", "rama")
