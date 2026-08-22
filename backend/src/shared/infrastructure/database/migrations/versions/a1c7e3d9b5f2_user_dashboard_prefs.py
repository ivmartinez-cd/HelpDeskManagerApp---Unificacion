"""auth: preferencias de Inicio por usuario (paneles ocultos + vista inicial), ADR-033

Revision ID: a1c7e3d9b5f2
Revises: f4b8e29c6d17
Create Date: 2026-08-23 00:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1c7e3d9b5f2"
down_revision: str | None = "f4b8e29c6d17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_dashboard_prefs",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "hidden_cards",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "initial_view", sa.String(length=16), server_default=sa.text("'hoy'"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_dashboard_prefs")
