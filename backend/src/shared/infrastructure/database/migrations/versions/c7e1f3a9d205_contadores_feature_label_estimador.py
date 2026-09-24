"""contadores_feature_label_estimador

Revision ID: c7e1f3a9d205
Revises: b4d8e2a6c913
Create Date: 2026-09-24 19:00:00.000000

La herramienta "Proyección" pasa a llamarse "Estimador de contadores" en la
UI. Esta migración cambia solo el texto que se ve del permiso: la clave
(`contadores-proyeccion-operar`) no cambia, así que los permisos ya otorgados
siguen valiendo.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7e1f3a9d205"
down_revision: str | None = "b4d8e2a6c913"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FEATURE_KEY = "contadores-proyeccion-operar"
_SQL = "UPDATE module_feature SET label = :label WHERE key = :key"
_LABEL_NUEVO = "Estimador de contadores: operar candidatos"
_LABEL_VIEJO = "Proyección: operar candidatos"


def upgrade() -> None:
    op.execute(sa.text(_SQL).bindparams(label=_LABEL_NUEVO, key=_FEATURE_KEY))


def downgrade() -> None:
    op.execute(sa.text(_SQL).bindparams(label=_LABEL_VIEJO, key=_FEATURE_KEY))
