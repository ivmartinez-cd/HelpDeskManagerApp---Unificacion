"""contadores_decision_operador_por_proceso

Revision ID: 72f9b126f6a9
Revises: f2c7a9d4b1e8
Create Date: 2026-09-24 12:00:00.000000

La decisión vigente del operador (Proyección de contadores) pasa a guardarse
por (nro_proceso, id_maquina, clase) y a registrar la ACCIÓN y sus insumos en
vez de un valor congelado, como el Estimador legacy: al cargar la grilla
restaura, por NroProceso, la última acción de cada fila desde su auditoría
(`GrillaEstimacion.RestaurarOverridesAsync`) y vuelve a correr el motor —
P/L manual con las lecturas elegidas (por `ID_Contador`), forzar con el
método, marcar pendiente — en vez de arrastrar un valor a los meses siguientes.
Sin columna `nota`: la observación del operador es solo de la auditoría
(`Estim_Log.Observacion` del legacy), no de la decisión.

Las filas existentes se BORRAN: no tienen proceso, así que no se pueden
atribuir a ninguno (eran datos de prueba de HDM cargados antes de este
cambio). La auditoría append-only (`contadores_estim_log`) no se toca. El
downgrade recrea el esquema anterior, vacío.
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "72f9b126f6a9"
down_revision: str | None = "f2c7a9d4b1e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLA = "contadores_decision_operador"


def _columnas_lectura(prefijo: str) -> list[sa.Column[Any]]:
    return [
        sa.Column(f"{prefijo}_id_contador", sa.Integer(), nullable=True),
        sa.Column(f"{prefijo}_fecha", sa.Date(), nullable=True),
        sa.Column(f"{prefijo}_valor", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column(f"{prefijo}_tipo_toma", sa.Integer(), nullable=True),
        sa.Column(f"{prefijo}_para_facturar", sa.Boolean(), nullable=True),
    ]


def upgrade() -> None:
    op.drop_table(_TABLA)
    op.create_table(
        _TABLA,
        sa.Column("nro_proceso", sa.Integer(), nullable=False),
        sa.Column("id_maquina", sa.Integer(), nullable=False),
        sa.Column("clase", sa.String(length=10), nullable=False),
        sa.Column("accion", sa.String(length=30), nullable=False),
        *_columnas_lectura("partida"),
        *_columnas_lectura("llegada"),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("nro_proceso", "id_maquina", "clase"),
    )


def downgrade() -> None:
    op.drop_table(_TABLA)
    op.create_table(
        _TABLA,
        sa.Column("id_maquina", sa.Integer(), nullable=False),
        sa.Column("clase", sa.String(length=10), nullable=False),
        sa.Column("pendiente", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("manual_contador_propuesto", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("manual_tipo_toma", sa.Integer(), nullable=True),
        sa.Column("manual_fuente", sa.String(length=40), nullable=True),
        sa.Column("manual_metodo_detalle", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id_maquina", "clase"),
    )
