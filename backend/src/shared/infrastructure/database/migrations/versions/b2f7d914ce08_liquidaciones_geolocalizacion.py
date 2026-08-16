"""liquidaciones geolocalización: km ida/vuelta, procedencia de coords,
cache de geocodes, resoluciones de sucursales sin pin y previews del cálculo.

Revision ID: b2f7d914ce08
Revises: a1b2c3d4e5f6
Create Date: 2026-08-15

Convención de km confirmada en Fase 0 (2026-08-15): `kms_recorrido` y
`kms_a_facturar` son el TOTAL ida+vuelta para todos los prestadores; los
tramos medidos por Google se guardan aparte en `kms_ida`/`kms_vuelta`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "b2f7d914ce08"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tabla_kms", sa.Column("kms_ida", sa.Float(), nullable=True))
    op.add_column("tabla_kms", sa.Column("kms_vuelta", sa.Float(), nullable=True))
    op.add_column("tabla_kms", sa.Column("coords_origen", sa.String(), nullable=True))
    op.add_column(
        "tabla_kms", sa.Column("geocode_formatted_address", sa.String(), nullable=True)
    )
    op.add_column(
        "tabla_kms", sa.Column("geocode_fecha", sa.DateTime(timezone=True), nullable=True)
    )
    _crear_geocode_cache()
    _crear_sucursal_coordenadas()
    _crear_calculo_km_previews()


def _crear_geocode_cache() -> None:
    op.create_table(
        "geocode_cache",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("direccion_normalizada", sa.String(), nullable=False, unique=True),
        sa.Column("candidatos", JSONB(), nullable=False),
        sa.Column(
            "fecha_consulta",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def _crear_sucursal_coordenadas() -> None:
    op.create_table(
        "sucursal_coordenadas",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "prestador_id",
            UUID(as_uuid=True),
            sa.ForeignKey("prestadores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("siges_sucursal_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("empresa_nombre", sa.String(), nullable=False),
        sa.Column("sucursal_nombre", sa.String(), nullable=False),
        sa.Column("direccion_normalizada", sa.String(), nullable=True),
        sa.Column("latitud", sa.Float(), nullable=True),
        sa.Column("longitud", sa.Float(), nullable=True),
        sa.Column("procedencia", sa.String(), nullable=True),
        sa.Column("formatted_address", sa.String(), nullable=True),
        sa.Column("fecha_resolucion", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index(
        "ix_sucursal_coordenadas_prestador_id", "sucursal_coordenadas", ["prestador_id"]
    )


def _crear_calculo_km_previews() -> None:
    op.create_table(
        "calculo_km_previews",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "prestador_id",
            UUID(as_uuid=True),
            sa.ForeignKey("prestadores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filas", JSONB(), nullable=False),
        sa.Column("sin_ubicar", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("sin_ruta", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "elementos_google", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("calculo_km_previews")
    op.drop_index("ix_sucursal_coordenadas_prestador_id", table_name="sucursal_coordenadas")
    op.drop_table("sucursal_coordenadas")
    op.drop_table("geocode_cache")
    op.drop_column("tabla_kms", "geocode_fecha")
    op.drop_column("tabla_kms", "geocode_formatted_address")
    op.drop_column("tabla_kms", "coords_origen")
    op.drop_column("tabla_kms", "kms_vuelta")
    op.drop_column("tabla_kms", "kms_ida")
