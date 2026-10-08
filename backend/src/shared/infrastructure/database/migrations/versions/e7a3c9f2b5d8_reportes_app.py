"""reportes_app: errores y mejoras cargados desde el botón "Reportar"

Revision ID: e7a3c9f2b5d8
Revises: d6b2e8f4a1c7
Create Date: 2026-10-08

Cada fila es un reporte de un usuario (tipo, detalle, pantalla donde estaba y
foto opcional en `var/reportes_app/fotos`). `estado`/`nota` los maneja el
servidor MCP `scripts/mcp/reportes_app_mcp.py`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "e7a3c9f2b5d8"
down_revision: str | None = "d6b2e8f4a1c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reportes_app",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False),
        sa.Column("ruta", sa.String(), nullable=False),
        sa.Column("foto", sa.String()),
        sa.Column(
            "usuario_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="SET NULL")
        ),
        sa.Column("estado", sa.String(), nullable=False, server_default="nuevo"),
        sa.Column("nota", sa.Text()),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("actualizado_en", sa.DateTime(timezone=True)),
        sa.CheckConstraint("tipo IN ('error', 'mejora')", name="ck_reportes_app_tipo"),
        sa.CheckConstraint(
            "estado IN ('nuevo', 'en_curso', 'resuelto', 'descartado')",
            name="ck_reportes_app_estado",
        ),
    )


def downgrade() -> None:
    op.drop_table("reportes_app")
