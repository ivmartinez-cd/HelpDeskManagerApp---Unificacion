"""vacaciones ausencias y auditoria

Revision ID: a7c3f81e42d9
Revises: d6e3c1b4a829
Create Date: 2026-08-13

Entrega 2 de vacaciones: tabla de bajas/ausencias (Absence legacy, 7 tipos +
medio día, nacen APPROVED) y log de auditoría del módulo (AuditLog legacy;
mismas strings de acción/entidad para que la futura migración de datos reales
quede uniforme).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "a7c3f81e42d9"
down_revision: str | None = "d6e3c1b4a829"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TIPOS = (
    "'DESCUENTO_DIA', 'BAJA_ENFERMEDAD', 'TRAMITE_PERSONAL', 'GUARDIA', "
    "'DIA_ESTUDIO', 'HOME_OFFICE', 'OTHER'"
)


def upgrade() -> None:
    op.create_table(
        "vacaciones_ausencia",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "empleado_id",
            UUID(as_uuid=True),
            sa.ForeignKey("vacaciones_empleado.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("days_count", sa.Integer(), nullable=False),
        sa.Column("half_day", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'APPROVED'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("end_date >= start_date", name="ck_vacaciones_ausencia_rango"),
        sa.CheckConstraint(f"tipo IN ({_TIPOS})", name="ck_vacaciones_ausencia_tipo"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_vacaciones_ausencia_status",
        ),
    )
    op.create_index(
        "ix_vacaciones_ausencia_empleado_id", "vacaciones_ausencia", ["empleado_id"]
    )
    op.create_index("ix_vacaciones_ausencia_tipo", "vacaciones_ausencia", ["tipo"])
    op.create_index("ix_vacaciones_ausencia_status", "vacaciones_ausencia", ["status"])
    op.create_index(
        "ix_vacaciones_ausencia_rango", "vacaciones_ausencia", ["start_date", "end_date"]
    )

    op.create_table(
        "vacaciones_audit_log",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("accion", sa.String(30), nullable=False),
        sa.Column("entidad", sa.String(40), nullable=False),
        sa.Column("entidad_id", sa.String(64), nullable=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("app_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_vacaciones_audit_log_accion", "vacaciones_audit_log", ["accion"])
    op.create_index("ix_vacaciones_audit_log_entidad", "vacaciones_audit_log", ["entidad"])
    op.create_index("ix_vacaciones_audit_log_user_id", "vacaciones_audit_log", ["user_id"])
    op.create_index(
        "ix_vacaciones_audit_log_created_at", "vacaciones_audit_log", ["created_at"]
    )


def downgrade() -> None:
    op.drop_table("vacaciones_audit_log")
    op.drop_table("vacaciones_ausencia")
