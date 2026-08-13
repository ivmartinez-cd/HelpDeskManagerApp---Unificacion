"""vacaciones schema

Revision ID: e8b2a5c91f47
Revises: d91f4b7a03c8
Create Date: 2026-08-13

Entrega 1 del módulo de vacaciones (migración de VacaSync):
- Extiende `department` (compartida con auth) con `color` — el ABM de Sectores
  de Gestión Humana opera sobre esa tabla, no sobre una propia.
- Crea las 8 tablas del módulo (prefijo `vacaciones_`), con fechas DATE (no
  timestamps: el legacy guardaba medianoche UTC y generaba off-by-one).
- Siembra el singleton `vacaciones_config` con los defaults del legacy (los
  7 tiers del default de Prisma, que es lo que tiene producción).
- Declara la acción `manage` para el módulo en `module_action` (la acción ya
  existe en el catálogo; el módulo quedó sembrado deshabilitado en
  4c741806341e_seed_catalog y se activa en una migración aparte al final).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e8b2a5c91f47"
down_revision: str | None = "d91f4b7a03c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_SENIORITY_TIERS = (
    '[{"min_years": 0, "max_years": 0.5, "days": 7},'
    ' {"min_years": 0.5, "max_years": 1, "days": 14},'
    ' {"min_years": 1, "max_years": 5, "days": 14},'
    ' {"min_years": 5, "max_years": 10, "days": 21},'
    ' {"min_years": 10, "max_years": 15, "days": 21},'
    ' {"min_years": 15, "max_years": 20, "days": 28},'
    ' {"min_years": 20, "max_years": 99, "days": 35}]'
)


def _ts(name: str) -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    op.add_column(
        "department",
        sa.Column("color", sa.String(), nullable=False, server_default=sa.text("'#3b82f6'")),
    )
    _create_catalogos()
    _create_empleado()
    _create_ciclo_y_solicitudes()
    _create_config_y_exclusiones()
    _seed()


def _create_catalogos() -> None:
    op.create_table(
        "vacaciones_cargo",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("max_simultaneos", sa.Integer(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.CheckConstraint(
            "max_simultaneos IS NULL OR max_simultaneos >= 1",
            name="ck_vacaciones_cargo_max_simultaneos",
        ),
    )
    op.create_table(
        "vacaciones_feriado",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "deducts_vacation", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )


def _create_empleado() -> None:
    op.create_table(
        "vacaciones_empleado",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column(
            "annual_vacation_days", sa.Integer(), server_default=sa.text("22"), nullable=False
        ),
        sa.Column("status", sa.String(), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column("color", sa.String(), server_default=sa.text("'#3b82f6'"), nullable=False),
        sa.Column("department_id", sa.UUID(), nullable=False),
        sa.Column("cargo_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("user_id"),
        sa.ForeignKeyConstraint(["department_id"], ["department.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cargo_id"], ["vacaciones_cargo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_vacaciones_empleado_status"
        ),
    )
    op.create_index(
        "ix_vacaciones_empleado_department_id", "vacaciones_empleado", ["department_id"]
    )
    op.create_index("ix_vacaciones_empleado_cargo_id", "vacaciones_empleado", ["cargo_id"])


def _create_ciclo_y_solicitudes() -> None:
    op.create_table(
        "vacaciones_ciclo",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("empleado_id", sa.UUID(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("annual_days", sa.Integer(), nullable=False),
        sa.Column("carry_over", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_open", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empleado_id", "year", name="uq_vacaciones_ciclo_empleado_year"),
        sa.ForeignKeyConstraint(["empleado_id"], ["vacaciones_empleado.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_vacaciones_ciclo_empleado_id", "vacaciones_ciclo", ["empleado_id"])
    op.create_index("ix_vacaciones_ciclo_year", "vacaciones_ciclo", ["year"])
    op.create_table(
        "vacaciones_solicitud",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("empleado_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("days_requested", sa.Integer(), nullable=False),
        sa.Column("charged_to_year", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'PENDING'"), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["empleado_id"], ["vacaciones_empleado.id"], ondelete="CASCADE"),
        sa.CheckConstraint("end_date >= start_date", name="ck_vacaciones_solicitud_rango"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')", name="ck_vacaciones_solicitud_status"
        ),
    )
    op.create_index("ix_vacaciones_solicitud_empleado_id", "vacaciones_solicitud", ["empleado_id"])
    op.create_index("ix_vacaciones_solicitud_status", "vacaciones_solicitud", ["status"])
    op.create_index(
        "ix_vacaciones_solicitud_charged_to_year", "vacaciones_solicitud", ["charged_to_year"]
    )
    op.create_index(
        "ix_vacaciones_solicitud_rango", "vacaciones_solicitud", ["start_date", "end_date"]
    )
    op.create_table(
        "vacaciones_aprobacion",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("solicitud_id", sa.UUID(), nullable=False),
        sa.Column("approver_user_id", sa.UUID(), nullable=True),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["solicitud_id"], ["vacaciones_solicitud.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approver_user_id"], ["app_user.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "decision IN ('APPROVED', 'REJECTED')", name="ck_vacaciones_aprobacion_decision"
        ),
    )
    op.create_index(
        "ix_vacaciones_aprobacion_solicitud_id", "vacaciones_aprobacion", ["solicitud_id"]
    )


def _create_config_y_exclusiones() -> None:
    op.create_table(
        "vacaciones_exclusion",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("empleado_a_id", sa.UUID(), nullable=False),
        sa.Column("empleado_b_id", sa.UUID(), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empleado_a_id", "empleado_b_id", name="uq_vacaciones_exclusion_par"),
        sa.ForeignKeyConstraint(["empleado_a_id"], ["vacaciones_empleado.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["empleado_b_id"], ["vacaciones_empleado.id"], ondelete="CASCADE"),
        sa.CheckConstraint("empleado_a_id < empleado_b_id", name="ck_vacaciones_exclusion_orden"),
    )
    op.create_table(
        "vacaciones_config",
        sa.Column("id", sa.String(), server_default=sa.text("'singleton'"), nullable=False),
        sa.Column("seniority_tiers", postgresql.JSONB(), nullable=False),
        sa.Column(
            "next_year_open_month", sa.Integer(), server_default=sa.text("10"), nullable=False
        ),
        sa.Column("next_year_open_day", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "allow_advance_request", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("max_advance_days", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("allow_carry_over", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "max_carry_over_days", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "min_advance_notice_days", sa.Integer(), server_default=sa.text("7"), nullable=False
        ),
        sa.Column(
            "max_overlap_percent", sa.Integer(), server_default=sa.text("50"), nullable=False
        ),
        sa.Column("max_overlap_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("id = 'singleton'", name="ck_vacaciones_config_singleton"),
    )


def _seed() -> None:
    op.execute(
        "INSERT INTO vacaciones_config (id, seniority_tiers) "
        f"VALUES ('singleton', '{_DEFAULT_SENIORITY_TIERS}'::jsonb) "
        "ON CONFLICT (id) DO NOTHING"
    )
    op.execute(
        "INSERT INTO module_action (module_key, action_key) VALUES ('vacaciones', 'manage') "
        "ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM module_action WHERE module_key = 'vacaciones' AND action_key = 'manage'"
    )
    op.drop_table("vacaciones_config")
    op.drop_table("vacaciones_exclusion")
    op.drop_table("vacaciones_aprobacion")
    op.drop_table("vacaciones_solicitud")
    op.drop_table("vacaciones_ciclo")
    op.drop_table("vacaciones_empleado")
    op.drop_table("vacaciones_feriado")
    op.drop_table("vacaciones_cargo")
    op.drop_column("department", "color")
