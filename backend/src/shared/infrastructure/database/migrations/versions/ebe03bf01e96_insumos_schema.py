"""insumos schema

Revision ID: ebe03bf01e96
Revises: 6d910a2b8e39
Create Date: 2026-08-10 19:26:48.496958

Migra el modelo de datos de SDSInsumos (legacy: SQLite, sin ORM, sin FKs) a Postgres.
Detalle completo con citas archivo:línea del legacy en
docs/sdsinsumos/SDSINSUMOS_CARACTERIZACION_BACKEND.md.
Notas de esta migración:

- PKs son IDs externos numéricos (de HP Insight / Canal Directo), no identidades que genera la
  app — van como BIGINT, no UUID (a diferencia de ftp_clients/meter_client_configs).
- Las 3 convenciones de fecha del legacy (ISO-Z de Insight, `datetime('now')` UTC de SQLite,
  `DD/MM/YYYY` de Canal Directo) colapsan todas a TIMESTAMPTZ acá.
- Sin foreign keys, a propósito: el legacy tampoco las tiene (confirmado, cero FK en las 14
  tablas) — endurecerlas es una decisión de un paso posterior, cuando el flujo de escritura
  completo esté portado.
- `order_claim` es tabla nueva, no existe en el legacy — reemplaza a `KeyedLock` (lock en
  memoria de un solo proceso) por un índice único parcial en Postgres.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ebe03bf01e96"
down_revision: str | None = "6d910a2b8e39"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers_config",
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("customer_id"),
    )

    op.create_table(
        "processed_requests",
        sa.Column("hp_request_id", sa.BigInteger(), nullable=False),
        sa.Column("device_id", sa.BigInteger(), nullable=True),
        sa.Column("device_serial", sa.String(), nullable=True),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("sku", sa.String(), nullable=True),
        sa.Column("internal_order_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("initial_percent_left", sa.Integer(), nullable=True),
        sa.Column("initial_days_left", sa.Integer(), nullable=True),
        sa.Column("initial_pages_left", sa.Integer(), nullable=True),
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
        sa.PrimaryKeyConstraint("hp_request_id"),
    )
    op.create_index(
        "idx_processed_serial_sku", "processed_requests", ["device_serial", "sku", "created_at"]
    )

    op.create_table(
        "supply_serial_cache",
        sa.Column("supply_id", sa.BigInteger(), nullable=False),
        sa.Column("serial", sa.String(), nullable=False),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("empresa_id", sa.String(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sku", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "cached_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("supply_id"),
    )
    op.create_index("ix_supply_serial_cache_serial", "supply_serial_cache", ["serial"])
    op.create_index(
        "idx_supply_cache_serial_lower",
        "supply_serial_cache",
        [sa.text("lower(serial)")],
        unique=False,
    )

    op.create_table(
        "supply_status_history",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("supply_id", sa.BigInteger(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supply_id", "estado"),
    )
    op.create_index("idx_supply_history_seen", "supply_status_history", ["first_seen_at"])

    op.create_table(
        "pending_order_notifications",
        sa.Column("hp_request_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "notified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("hp_request_id"),
    )

    op.create_table(
        "scan_checkpoint",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "customer_zone_contacts",
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("zone", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("sol_apellido", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("sol_nombre", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("sol_telefono", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("sol_email", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("sol_sector", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("dest_apellido", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("dest_nombre", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("dest_telefono", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("dest_email", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("dest_sector", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("observaciones", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.PrimaryKeyConstraint("customer_id", "zone"),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "order_audit",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("hp_request_id", sa.BigInteger(), nullable=True),
        sa.Column("device_id", sa.BigInteger(), nullable=True),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("customer_name", sa.String(), nullable=True),
        sa.Column("device_serial", sa.String(), nullable=True),
        sa.Column("sku", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("internal_order_id", sa.String(), nullable=True),
        sa.Column("order_type", sa.String(), server_default=sa.text("'supply'"), nullable=False),
        sa.Column("detail", sa.String(), nullable=True),
        sa.Column("dry_run", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("hp_request_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initial_percent_left", sa.Integer(), nullable=True),
        sa.Column("initial_days_left", sa.Integer(), nullable=True),
        sa.Column("initial_pages_left", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_created", "order_audit", ["created_at"])
    op.create_index("idx_audit_customer_created", "order_audit", ["customer_id", "created_at"])
    op.create_index("idx_audit_hp_request_id", "order_audit", ["hp_request_id"])

    op.create_table(
        "known_devices",
        sa.Column("device_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("serial", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("model", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("zone", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("ip_address", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("monitor_status", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("monitor_name", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("discovery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contact", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "first_seen_at",
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
        sa.Column("dismissed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "offline_dismissed", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("cd_status", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("cd_detail", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("cd_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("device_id"),
    )
    op.create_index("idx_known_devices_status", "known_devices", ["monitor_status"])
    op.create_index("idx_known_devices_last_contact", "known_devices", ["last_contact"])

    op.create_table(
        "dca_monitors",
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("monitor_name", sa.String(), nullable=False),
        sa.Column("online", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("last_contact", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("customer_id", "monitor_name"),
    )

    op.create_table(
        "request_alerts",
        sa.Column("hp_request_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("customer_name", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("device_serial", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("sku", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("description", sa.String(), server_default=sa.text("''"), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("state", sa.String(), server_default=sa.text("'TRIGGERED'"), nullable=False),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("hp_request_id"),
    )
    op.create_index("idx_request_alerts_state", "request_alerts", ["state"])

    op.create_table(
        "mail_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("recipients", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_mail_log_sent_at", "mail_log", ["sent_at"])

    op.create_table(
        "request_validations",
        sa.Column("hp_request_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("device_id", sa.BigInteger(), nullable=False),
        sa.Column("device_serial", sa.String(), nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("initial_percent_left", sa.Double(), nullable=True),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("swap_note", sa.String(), nullable=True),
        sa.Column("swap_checked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("diagnosis_headline", sa.String(), nullable=True),
        sa.Column("diagnosis_detail", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("hp_request_id"),
    )
    op.create_index("idx_request_validations_due", "request_validations", ["status", "deadline_at"])

    # Mecanismo de idempotencia nuevo (reemplaza KeyedLock) — ver
    # domain/services/claimed_order_creation.py.
    op.create_table(
        "order_claim",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("device_serial", sa.String(), nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'IN_PROGRESS'"), nullable=False),
        sa.Column(
            "claimed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_order_claim_in_progress",
        "order_claim",
        ["device_serial", "sku"],
        unique=True,
        postgresql_where=sa.text("status = 'IN_PROGRESS'"),
    )


def downgrade() -> None:
    op.drop_table("order_claim")
    op.drop_table("request_validations")
    op.drop_table("mail_log")
    op.drop_table("request_alerts")
    op.drop_table("dca_monitors")
    op.drop_table("known_devices")
    op.drop_table("order_audit")
    op.drop_table("app_settings")
    op.drop_table("customer_zone_contacts")
    op.drop_table("scan_checkpoint")
    op.drop_table("pending_order_notifications")
    op.drop_table("supply_status_history")
    op.drop_table("supply_serial_cache")
    op.drop_table("processed_requests")
    op.drop_table("customers_config")
