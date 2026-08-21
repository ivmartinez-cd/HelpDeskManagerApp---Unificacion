"""user_route_visit -- tracking de accesos directos por usuario (ADR-028)

Revision ID: c2f8a91d4e73
Revises: e7a4c1f6b823
Create Date: 2026-08-20 00:00:00.000000

Contador agregado por (usuario, día, ruta), no un event log -- ver ADR-028
para el razonamiento completo (por qué no hay permiso module/action nuevo,
por qué la feature vive en el módulo `auth`, por qué es un contador
agregado con upsert en vez de una fila por navegación).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "c2f8a91d4e73"
down_revision: str | None = "e7a4c1f6b823"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_route_visit",
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("app_user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("visit_date", sa.Date(), primary_key=True),
        sa.Column("route", sa.String(128), primary_key=True),
        sa.Column(
            "visit_count", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
        sa.CheckConstraint("visit_count > 0", name="ck_user_route_visit_count_positive"),
        sa.CheckConstraint(
            "route ~ '^(/[a-z][a-z0-9]*(-[a-z0-9]+)*){1,4}$'",
            name="ck_user_route_visit_route_format",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_route_visit")
