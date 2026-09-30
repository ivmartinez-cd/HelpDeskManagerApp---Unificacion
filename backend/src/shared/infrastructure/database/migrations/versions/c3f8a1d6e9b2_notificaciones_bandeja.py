"""notificaciones: bandeja in-app + función "Avisos de Mesa de Ayuda"

Revision ID: c3f8a1d6e9b2
Revises: b4e7c2a9d1f6
Create Date: 2026-09-30

Bandeja de notificaciones de la app (campanita del header): `notificaciones`
guarda cada aviso una vez, dirigido a una audiencia (función o permiso), y
`notificaciones_lecturas` quién lo leyó. Primer productor: el job de SLA que
detecta casos de Mesa de Ayuda con una visita de técnico en la misma sucursal,
dirigido a la función nueva `sla-avisos-mesa-ayuda` (sin backfill: se concede
por persona desde Permisos; el superadmin la recibe siempre).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "c3f8a1d6e9b2"
down_revision: str | None = "b4e7c2a9d1f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FEATURE_KEY = "sla-avisos-mesa-ayuda"


def _crear_tablas() -> None:
    op.create_table(
        "notificaciones",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("clave", sa.String(), nullable=False, unique=True),
        sa.Column("audiencia", sa.String(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("url", sa.String()),
        sa.Column(
            "creada_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index(
        "ix_notificaciones_audiencia_creada", "notificaciones", ["audiencia", "creada_en"]
    )
    op.create_table(
        "notificaciones_lecturas",
        sa.Column(
            "notificacion_id",
            UUID(as_uuid=True),
            sa.ForeignKey("notificaciones.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "usuario_id",
            UUID(as_uuid=True),
            sa.ForeignKey("app_user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "leida_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )


def _sembrar_funcion() -> None:
    feature = sa.table(
        "module_feature",
        sa.column("key", sa.String),
        sa.column("module_key", sa.String),
        sa.column("label", sa.String),
        sa.column("description", sa.String),
        sa.column("sort_order", sa.SmallInteger),
    )
    op.bulk_insert(
        feature,
        [
            {
                "key": FEATURE_KEY,
                "module_key": "sla",
                "label": "Avisos de Mesa de Ayuda",
                "description": (
                    "Recibe en la campanita los casos de Mesa de Ayuda con una visita "
                    "de técnico en marcha en la misma sucursal."
                ),
                "sort_order": 10,
            }
        ],
    )


def upgrade() -> None:
    _crear_tablas()
    _sembrar_funcion()


def downgrade() -> None:
    # user_feature_grant cae en cascada por la FK a module_feature.
    op.execute(sa.text("DELETE FROM module_feature WHERE key = :k").bindparams(k=FEATURE_KEY))
    op.drop_table("notificaciones_lecturas")
    op.drop_index("ix_notificaciones_audiencia_creada", table_name="notificaciones")
    op.drop_table("notificaciones")
