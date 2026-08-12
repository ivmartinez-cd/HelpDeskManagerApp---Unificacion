"""liquidaciones schema core

Revision ID: b74bde547b01
Revises: 772de77d6ec0
Create Date: 2026-08-12 18:46:46.247771

Migra el modelo de datos de referencia de Liquidacion-Prestadores (legacy: SQLite, FKs
sin `ondelete`) a Postgres. Detalle completo en
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` en la raíz del repo. Notas:

- PKs son UUID generadas por la app (`gen_random_uuid()`), no los IDs autoincrement
  del legacy — mismo patrón que contadores/turnos/auth (a diferencia de insumos, cuyos
  PKs son IDs externos de HP Insight/Canal Directo).
- La integración WS AyC del legacy (rama `feature/ws-ayc-liquidaciones`, nunca
  desplegada — ver §6 del doc de caracterización) queda fuera de esta migración: sin
  columnas `ayc_*`.
- Esta migración cubre los datos de referencia (catálogo de prestadores/tarifas/reglas);
  `0468811de473_liquidaciones_schema_transacciones` cubre el workflow de liquidaciones
  propiamente dicho, separado para no superar el límite de 300 líneas por archivo.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "b74bde547b01"
down_revision: str | None = "772de77d6ec0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prestadores",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("nombre_corto", sa.String(), nullable=False),
        sa.Column("cuit", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre_corto"),
    )

    op.create_table(
        "spsts",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("domicilio", sa.String(), nullable=True),
        sa.Column("localidad", sa.String(), nullable=True),
        sa.Column("provincia", sa.String(), nullable=True),
        sa.Column("zona", sa.String(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestadores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tarifarios",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("tipo_servicio", sa.String(), nullable=False),
        sa.Column("zona", sa.String(), nullable=True),
        sa.Column("costo_servicio", sa.Float(), nullable=False),
        sa.Column("costo_km", sa.Float(), nullable=False),
        sa.Column("vigencia_desde", sa.Date(), nullable=False),
        sa.Column("vigencia_hasta", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestadores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tabla_kms",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("spst_id", sa.UUID(), nullable=True),
        sa.Column("empresa_nombre", sa.String(), nullable=False),
        sa.Column("sucursal_nombre", sa.String(), nullable=False),
        sa.Column("observaciones", sa.String(), nullable=True),
        sa.Column("domicilio_cliente", sa.String(), nullable=True),
        sa.Column("localidad_cliente", sa.String(), nullable=True),
        sa.Column("provincia_cliente", sa.String(), nullable=True),
        sa.Column("kms_recorrido", sa.Float(), nullable=False),
        sa.Column("umbral_viatico", sa.Float(), server_default=sa.text("30.0"), nullable=False),
        sa.Column("aplica_viatico", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("kms_a_facturar", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("url_maps", sa.String(), nullable=True),
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
        sa.ForeignKeyConstraint(["prestador_id"], ["prestadores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["spst_id"], ["spsts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reglas_alerta",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("codigo", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("activa", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("riesgo_base", sa.Float(), nullable=False),
        sa.Column(
            "configuracion",
            JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )


def downgrade() -> None:
    op.drop_table("reglas_alerta")
    op.drop_table("tabla_kms")
    op.drop_table("tarifarios")
    op.drop_table("spsts")
    op.drop_table("prestadores")
