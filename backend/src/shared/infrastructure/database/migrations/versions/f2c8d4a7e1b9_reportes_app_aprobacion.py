"""reportes_app: circuito de aprobación (propuesta de Claude + OK de Iván)

Revision ID: f2c8d4a7e1b9
Revises: e7a3c9f2b5d8
Create Date: 2026-10-08

Estados nuevos `propuesto` (Claude dejó diagnóstico y propuesta en `nota`) y
`aprobado` (el superadmin dio el OK desde el panel). `respuesta` guarda el
comentario del superadmin al aprobar, pedir cambios o descartar.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2c8d4a7e1b9"
down_revision: str | None = "e7a3c9f2b5d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CK = "ck_reportes_app_estado"


def upgrade() -> None:
    op.add_column("reportes_app", sa.Column("respuesta", sa.Text()))
    op.drop_constraint(_CK, "reportes_app", type_="check")
    op.create_check_constraint(
        _CK,
        "reportes_app",
        "estado IN ('nuevo', 'propuesto', 'aprobado', 'en_curso', 'resuelto', 'descartado')",
    )


def downgrade() -> None:
    op.execute("UPDATE reportes_app SET estado = 'nuevo' WHERE estado IN ('propuesto', 'aprobado')")
    op.drop_constraint(_CK, "reportes_app", type_="check")
    op.create_check_constraint(
        _CK, "reportes_app", "estado IN ('nuevo', 'en_curso', 'resuelto', 'descartado')"
    )
    op.drop_column("reportes_app", "respuesta")
