"""liquidaciones alertas incidente relacionado

Revision ID: a1c7e2f4b9d3
Revises: 13b8777b84d0
Create Date: 2026-09-02

Vínculo estructurado entre una alerta ALT002 y el incidente donde en
realidad se cobraron los km de una ruta compartida — hasta ahora esa
relación solo quedaba anotada como texto libre en `justificacion` al
descartar la alerta a mano.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1c7e2f4b9d3"
down_revision: str | None = "13b8777b84d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "alertas",
        sa.Column("incidente_relacionado_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_alertas_incidente_relacionado_id",
        "alertas",
        "incidentes",
        ["incidente_relacionado_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_alertas_incidente_relacionado_id", "alertas", type_="foreignkey")
    op.drop_column("alertas", "incidente_relacionado_id")
