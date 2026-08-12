"""liquidaciones schema transacciones

Revision ID: 0468811de473
Revises: b74bde547b01
Create Date: 2026-08-12 18:46:47.904141

Workflow de liquidaciones propiamente dicho (liquidaciones → incidentes → alertas →
resoluciones, y observaciones agrupadas para ALT005). Ver
`b74bde547b01_liquidaciones_schema_core` para las notas generales de esta migración
(PKs UUID, WS AyC fuera de alcance).

Sin `ondelete` en `liquidaciones.prestador_id` a propósito: borrar un prestador con
liquidaciones existentes queda bloqueado — es historial de facturación real. El resto
de las FK de este archivo sí cascadean (`incidentes`→`liquidaciones`, `alertas`→
`incidentes`/`liquidaciones`, `resoluciones`→`alertas`, `observaciones`→`liquidaciones`,
`observacion_incidentes`→`observaciones`/`incidentes`), igual que el `cascade="all,
delete-orphan"` del ORM legacy.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0468811de473"
down_revision: str | None = "b74bde547b01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "liquidaciones",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("prestador_id", sa.UUID(), nullable=False),
        sa.Column("numero_liquidacion", sa.String(), nullable=True),
        sa.Column("periodo", sa.String(), nullable=False),
        sa.Column(
            "tipo_liquidacion", sa.String(), server_default=sa.text("'regular'"), nullable=False
        ),
        sa.Column("nombre_archivo", sa.String(), nullable=True),
        sa.Column(
            "fecha_importacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("estado", sa.String(), server_default=sa.text("'abierta'"), nullable=False),
        sa.Column("total_incidentes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_alertas", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_importe", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.ForeignKeyConstraint(["prestador_id"], ["prestadores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "incidentes",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("liquidacion_id", sa.UUID(), nullable=False),
        sa.Column("numero_incidente", sa.String(), nullable=False),
        sa.Column("rubro", sa.String(), nullable=True),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("empresa_nombre", sa.String(), nullable=True),
        sa.Column("sucursal_nombre", sa.String(), nullable=True),
        sa.Column("nro_serie", sa.String(), nullable=True),
        sa.Column("fecha_cierre", sa.Date(), nullable=True),
        sa.Column(
            "costo_servicio_cobrado", sa.Float(), server_default=sa.text("0.0"), nullable=False
        ),
        sa.Column("cant_km_cobrado", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("costo_km_cobrado", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("total_viaje_cobrado", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("costo_total_cobrado", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("pasa_it", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("costo_servicio_esperado", sa.Float(), nullable=True),
        sa.Column("cant_km_esperado", sa.Float(), nullable=True),
        sa.Column("costo_km_esperado", sa.Float(), nullable=True),
        sa.Column(
            "estado_validacion", sa.String(), server_default=sa.text("'pendiente'"), nullable=False
        ),
        sa.ForeignKeyConstraint(["liquidacion_id"], ["liquidaciones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_incidentes_numero", "incidentes", ["numero_incidente"])

    op.create_table(
        "alertas",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("incidente_id", sa.UUID(), nullable=False),
        sa.Column("liquidacion_id", sa.UUID(), nullable=False),
        sa.Column("tipo_alerta", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("datos_contexto", JSONB(), nullable=True),
        sa.Column("riesgo", sa.Float(), nullable=False),
        sa.Column("estado", sa.String(), server_default=sa.text("'pendiente'"), nullable=False),
        sa.Column(
            "fecha_generacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["incidente_id"], ["incidentes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["liquidacion_id"], ["liquidaciones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "resoluciones",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("alerta_id", sa.UUID(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("justificacion", sa.String(), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["alerta_id"], ["alertas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "observaciones",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("liquidacion_id", sa.UUID(), nullable=False),
        sa.Column("tipo_observacion", sa.String(), nullable=False),
        sa.Column("severidad", sa.String(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("datos_contexto", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("monto_cobrado", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("monto_esperado", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("diferencia", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("estado", sa.String(), server_default=sa.text("'pendiente'"), nullable=False),
        sa.Column("regla_codigo", sa.String(), nullable=True),
        sa.Column(
            "fecha_generacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["liquidacion_id"], ["liquidaciones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "observacion_incidentes",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("observacion_id", sa.UUID(), nullable=False),
        sa.Column("incidente_id", sa.UUID(), nullable=False),
        sa.Column("rol", sa.String(), server_default=sa.text("'referencia'"), nullable=False),
        sa.ForeignKeyConstraint(["observacion_id"], ["observaciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incidente_id"], ["incidentes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("observacion_incidentes")
    op.drop_table("observaciones")
    op.drop_table("resoluciones")
    op.drop_table("alertas")
    op.drop_index("idx_incidentes_numero", table_name="incidentes")
    op.drop_table("incidentes")
    op.drop_table("liquidaciones")
