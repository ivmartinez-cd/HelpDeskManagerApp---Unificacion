"""reporte_incidentes: tablas de taxonomía y caché de tipificación + catálogo

Revision ID: d1a4c8e2f6b3
Revises: c7e1f3a9d205
Create Date: 2026-09-25 12:00:00.000000

Port del legacy `reporte-incidentes`: la taxonomía (`categories.json`) pasa a
dos tablas y se siembra con la del legacy tal cual; la caché de tipificaciones
(`classification-cache.json`, textos de incidentes reales) NO viaja en la
migración: se importa aparte con `scripts/importar_tipificaciones_reporte_incidentes.py`.

El módulo queda en el catálogo DESHABILITADO hasta que el frontend esté
probado (mismo criterio de dos pasos que sla/contadores).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "d1a4c8e2f6b3"
down_revision: str | None = "c7e1f3a9d205"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MODULE_KEY = "reporte-incidentes"
_MODULE = {
    "key": _MODULE_KEY, "label": "Reporte de Incidentes", "route": "/reporte-incidentes",
    "icon": "activity", "sort_order": 42, "is_enabled": False,
}
_ACTIONS = ("view", "update")

# Taxonomía viva del legacy (src/lib/data/categories.json al 2026-09-25).
_TAXONOMIA: list[tuple[str, str, str, list[str]]] = [
    (
        "Medio de Impresion", "#f0a400",
        "Problemas del papel y las bandejas: atascos, papel troquelado mal cortado/humedo, "
        "papel inadecuado, arrugas/toma de varias hojas, ajuste de guias o bandejas.",
        [
            "Atasco de papel (comun)", "Papel especial / Troquelado",
            "Papel inadecuado / humedad / mala calidad", "Arruga / Toma varias hojas",
            "Ajuste de bandejas / guias", "Otros - Medio de Impresion",
        ],
    ),
    (
        "Insumos y Toner", "#e8743b",
        "Consumibles: cambio de toner/cartucho, vaciado de tolva/contenedor residual, "
        "drum/unidad de imagen/revelador, o calidad de impresion por insumo (manchas, "
        "impresion clara).",
        [
            "Toner / Cartucho", "Tolva / Contenedor residual",
            "Drum / Unidad de imagen / Revelador",
            "Calidad por insumo (manchas / impresion clara)", "Otros - Insumos y Toner",
        ],
    ),
    (
        "Hardware y Desgaste", "#0275d8",
        "Reemplazo o reparacion de piezas fisicas por desgaste/rotura: fusor/kit, rodillos "
        "pickup/retard/separacion, escaner/ADF, panel/botonera/partes rotas.",
        [
            "Rodillos / Pickup / Separacion", "Fusor / Kit de mantenimiento", "Escaner / ADF",
            "Parte / Panel / Botonera rota", "Otros - Hardware y Desgaste",
        ],
    ),
    (
        "Software, Firmware y Red", "#7b61ff",
        "Configuracion de red/IP, driver/PC/spooler, firmware, o calibracion/ajuste de "
        "imagen. Incluye configurar (aunque sea guiando al usuario en remoto).",
        [
            "Configuracion de red / IP", "Driver / PC / Spooler", "Firmware",
            "Calibracion / Ajuste de imagen", "Otros - Software, Firmware y Red",
        ],
    ),
    (
        "Gestion de Soporte", "#4dc247",
        "Casos sin reparacion tecnica de fondo: mesa de ayuda sin respuesta del cliente, "
        "instructivo/autoresolucion, mal uso/negligencia, diagnostico sin falla, "
        "mantenimiento/limpieza general, problema externo (red del cliente),RD (recambio "
        "definitivo).",
        [
            "Mesa de ayuda / Sin respuesta del cliente", "Instructivo / Autoresolucion",
            "Mal uso / Negligencia", "Diagnostico / Sin falla",
            "Mantenimiento / Limpieza general", "Problema externo / Red del cliente",
            "Otros - Gestion de Soporte", "Recambio Definitivo",
        ],
    ),
]

_module = sa.table(
    "module",
    sa.column("key", sa.String), sa.column("label", sa.String), sa.column("route", sa.String),
    sa.column("icon", sa.String), sa.column("sort_order", sa.SmallInteger),
    sa.column("is_enabled", sa.Boolean),
)
_module_action = sa.table(
    "module_action", sa.column("module_key", sa.String), sa.column("action_key", sa.String)
)


def _crear_tablas() -> None:
    op.create_table(
        "reporte_incidentes_categoria",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("color", sa.String(9), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=False),
        sa.Column("orden", sa.SmallInteger, nullable=False),
    )
    op.create_index(
        "uq_reporte_incidentes_categoria_nombre", "reporte_incidentes_categoria",
        [sa.text("lower(nombre)")], unique=True,
    )
    op.create_table(
        "reporte_incidentes_subcategoria",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "categoria_id", sa.Integer,
            sa.ForeignKey("reporte_incidentes_categoria.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("orden", sa.SmallInteger, nullable=False),
        sa.UniqueConstraint("categoria_id", "nombre", name="uq_reporte_incidentes_subcategoria"),
    )
    op.create_table(
        "reporte_incidentes_tipificacion",
        sa.Column("clave_hash", sa.String(64), primary_key=True),
        sa.Column("clave", sa.Text, nullable=False),
        sa.Column("categoria", sa.String(120), nullable=False),
        sa.Column("subcategoria", sa.String(160), nullable=False),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("origen", sa.String(10), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def _sembrar_taxonomia() -> None:
    bind = op.get_bind()
    for orden, (nombre, color, descripcion, subcategorias) in enumerate(_TAXONOMIA):
        categoria_id = bind.execute(
            sa.text(
                "INSERT INTO reporte_incidentes_categoria (nombre, color, descripcion, orden) "
                "VALUES (:n, :c, :d, :o) RETURNING id"
            ),
            {"n": nombre, "c": color, "d": descripcion, "o": orden},
        ).scalar_one()
        bind.execute(
            sa.text(
                "INSERT INTO reporte_incidentes_subcategoria (categoria_id, nombre, orden) "
                "VALUES (:cid, :n, :o)"
            ),
            [{"cid": categoria_id, "n": s, "o": i} for i, s in enumerate(subcategorias)],
        )


def _sembrar_catalogo() -> None:
    bind = op.get_bind()
    bind.execute(pg_insert(_module).on_conflict_do_nothing(index_elements=["key"]), [_MODULE])
    bind.execute(
        pg_insert(_module_action).on_conflict_do_nothing(
            index_elements=["module_key", "action_key"]
        ),
        [{"module_key": _MODULE_KEY, "action_key": a} for a in _ACTIONS],
    )


def upgrade() -> None:
    _crear_tablas()
    _sembrar_taxonomia()
    _sembrar_catalogo()


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(_module_action.delete().where(_module_action.c.module_key == _MODULE_KEY))
    bind.execute(_module.delete().where(_module.c.key == _MODULE_KEY))
    op.drop_table("reporte_incidentes_tipificacion")
    op.drop_table("reporte_incidentes_subcategoria")
    op.drop_index("uq_reporte_incidentes_categoria_nombre", "reporte_incidentes_categoria")
    op.drop_table("reporte_incidentes_categoria")
