"""insumos dismiss client mail

Revision ID: 73be3bdccdf5
Revises: 5668c18e0155
Create Date: 2026-08-28 14:25:13.461771

Porta el delta de SDSInsumos legacy (commits 9b72a47..2730477, ver
docs/sdsinsumos/SDSINSUMOS_MIGRACION_ESTADO.md): descarte persistente de pedidos
despachados sin confirmar entrega (dismissed_supplies), aviso a logística deduplicado
(dispatch_unconfirmed_notifications), y matching/aviso al cliente por consumable_serial
(processed_requests.consumable_serial/consumable_colour, customers_config.client_mail_enabled).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "73be3bdccdf5"
down_revision: str | None = "5668c18e0155"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "processed_requests", sa.Column("consumable_serial", sa.String(), nullable=True)
    )
    op.add_column(
        "processed_requests", sa.Column("consumable_colour", sa.String(), nullable=True)
    )
    op.create_index(
        "idx_processed_consumable_serial",
        "processed_requests",
        ["consumable_serial"],
    )

    op.add_column(
        "customers_config",
        sa.Column(
            "client_mail_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )

    op.create_table(
        "dispatch_unconfirmed_notifications",
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
        "dismissed_supplies",
        sa.Column("supply_id", sa.BigInteger(), nullable=False),
        sa.Column("device_serial", sa.String(), nullable=False),
        sa.Column("hp_request_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "dismissed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("supply_id"),
    )


def downgrade() -> None:
    op.drop_table("dismissed_supplies")
    op.drop_table("dispatch_unconfirmed_notifications")
    op.drop_column("customers_config", "client_mail_enabled")
    op.drop_index("idx_processed_consumable_serial", table_name="processed_requests")
    op.drop_column("processed_requests", "consumable_colour")
    op.drop_column("processed_requests", "consumable_serial")
