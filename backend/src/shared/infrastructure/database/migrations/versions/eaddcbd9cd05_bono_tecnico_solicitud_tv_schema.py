"""bono tecnico solicitud tv schema

Revision ID: eaddcbd9cd05
Revises: 9968df7a921d
Create Date: 2026-08-24 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "eaddcbd9cd05"
down_revision: str | None = "9968df7a921d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bono_tecnico_solicitud_tv",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("id_tecnico", sa.Integer(), nullable=False),
        sa.Column("tecnico", sa.String(length=120), nullable=False),
        sa.Column("periodo", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("razon_social", sa.String(length=200), nullable=False),
        sa.Column("sucursal", sa.String(length=200), nullable=False),
        sa.Column("tarea_realizada", sa.String(length=2000), nullable=False),
        sa.Column(
            "estado", sa.String(), nullable=False, server_default=sa.text("'PENDIENTE'")
        ),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resuelta_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resuelta_por_email", sa.String(length=255), nullable=True),
        sa.Column("motivo_rechazo", sa.String(length=500), nullable=True),
        sa.CheckConstraint(
            "estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')",
            name="ck_bono_tecnico_solicitud_tv_estado",
        ),
    )
    op.create_index(
        "ix_bono_tecnico_solicitud_tv_id_tecnico",
        "bono_tecnico_solicitud_tv",
        ["id_tecnico"],
    )
    op.create_index(
        "ix_bono_tecnico_solicitud_tv_estado", "bono_tecnico_solicitud_tv", ["estado"]
    )
    op.create_index(
        "ix_bono_tecnico_solicitud_tv_periodo_tecnico",
        "bono_tecnico_solicitud_tv",
        ["periodo", "id_tecnico"],
    )


def downgrade() -> None:
    op.drop_table("bono_tecnico_solicitud_tv")
