"""analisis_log_hp schema

Revision ID: a3c8e2f1b9d5
Revises: f2b4d6e8a0c1
Create Date: 2026-08-15 00:00:00.000000

Tablas del módulo analisis-log-hp (análisis de logs HP):
  pi_error_codes             — catálogo de códigos de error HP
  pi_saved_analyses          — snapshots de análisis con diagnóstico IA
  pi_device_telemetry_events — historial de telemetría por serial (motor de salud)

No activa el módulo: is_enabled queda en false hasta la entrega final
(mismo patrón que liquidaciones y otros módulos).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "a3c8e2f1b9d5"
down_revision: str | None = "f2b4d6e8a0c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pi_error_codes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("severity", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("solution_url", sa.Text),
        sa.Column("solution_content", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_pi_error_codes_code", "pi_error_codes", ["code"], unique=True)

    op.create_table(
        "pi_saved_analyses",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("equipment_identifier", sa.Text),
        sa.Column("incidents", JSONB, nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "global_severity",
            sa.Text,
            nullable=False,
            server_default=sa.text("'INFO'"),
        ),
        sa.Column("ai_diagnosis", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_pi_saved_analyses_created_at", "pi_saved_analyses", ["created_at"]
    )

    op.create_table(
        "pi_device_telemetry_events",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("device_serial", sa.Text, nullable=False),
        sa.Column("saved_analysis_id", UUID(as_uuid=True)),
        sa.Column("code", sa.Text, nullable=False),
        sa.Column("classification", sa.Text),
        sa.Column(
            "severity",
            sa.Text,
            nullable=False,
            server_default=sa.text("'INFO'"),
        ),
        sa.Column(
            "occurrences",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "counter",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_pi_telemetry_serial_time",
        "pi_device_telemetry_events",
        ["device_serial", "event_time"],
    )
    op.create_index(
        "ix_pi_telemetry_serial_code",
        "pi_device_telemetry_events",
        ["device_serial", "code"],
    )


def downgrade() -> None:
    op.drop_table("pi_device_telemetry_events")
    op.drop_table("pi_saved_analyses")
    op.drop_table("pi_error_codes")
