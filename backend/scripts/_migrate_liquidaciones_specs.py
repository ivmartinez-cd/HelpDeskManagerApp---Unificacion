"""Specs de columnas por tabla para `migrate_liquidaciones_data_from_sqlite.py`.

Separado del script principal por el límite de 300 líneas (`ARCHITECTURE_GUIDE.md` §4).
Cada `TablaSpec` declara, para UNA tabla legacy -> modelo nuevo: qué columnas leer de
SQLite (idénticas 1:1 en nombre al modelo, salvo `id`, que siempre se remapea a UUID —
ver `LIQUIDACION_PRESTADORES_CARACTERIZACION.md` y el gap analysis de la migración: no
hay renombres ni columnas nuevas entre legacy y nuevo, solo el cambio de tipo de PK/FK),
cuáles son FKs a remapear, booleanos 0/1, JSON-como-texto, fechas y timestamps.

`reglas_alerta` no tiene spec acá: es catálogo, se siembra por Alembic
(`17663a83c3fd_seed_liquidaciones_reglas_alerta.py`), no por este script.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from src.modules.liquidaciones.infrastructure.models.alerta_model import AlertaModel
from src.modules.liquidaciones.infrastructure.models.incidente_model import IncidenteModel
from src.modules.liquidaciones.infrastructure.models.liquidacion_model import LiquidacionModel
from src.modules.liquidaciones.infrastructure.models.prestador_model import (
    LiquidacionPrestadorModel,
)
from src.modules.liquidaciones.infrastructure.models.resolucion_model import ResolucionModel
from src.modules.liquidaciones.infrastructure.models.spst_model import SpstModel
from src.modules.liquidaciones.infrastructure.models.tabla_km_model import TablaKmModel
from src.modules.liquidaciones.infrastructure.models.tarifario_model import TarifarioModel

PostProcesar = Callable[[dict[str, Any], Any, dict[str, dict[int, UUID]]], None]


@dataclass(frozen=True)
class TablaSpec:
    origen: str
    modelo: type
    columnas: tuple[str, ...]
    fks: dict[str, str] = field(default_factory=dict)
    bools: tuple[str, ...] = ()
    bool_defaults: dict[str, bool] = field(default_factory=dict)
    jsons: tuple[str, ...] = ()
    json_defaults: dict[str, dict[str, Any]] = field(default_factory=dict)
    fechas: tuple[str, ...] = ()
    timestamps: tuple[str, ...] = ()
    post_procesar: PostProcesar | None = None


def _remap_ids_en_contexto_alerta(
    kwargs: dict[str, Any], row: Any, mapas: dict[str, dict[int, UUID]]
) -> None:
    """`alertas.datos_contexto` trae, en dos de sus claves, IDs legacy INTEGER embebidos
    en el JSON que el motor genera como texto libre: `spst_id` (ALT005) y
    `liquidaciones_previas` (lista, ALT004). El resto de las claves (montos, nombres,
    `numero_incidente`) son dato de negocio y sobreviven sin tocar."""
    datos = kwargs.get("datos_contexto")
    if not datos:
        return
    if datos.get("spst_id") is not None:
        nuevo = mapas["spsts"].get(datos["spst_id"])
        datos["spst_id"] = str(nuevo) if nuevo is not None else None
    if "liquidaciones_previas" in datos:
        datos["liquidaciones_previas"] = [
            str(mapas["liquidaciones"][lid])
            for lid in datos["liquidaciones_previas"]
            if lid in mapas["liquidaciones"]
        ]


ORDEN_TOPOLOGICO: tuple[TablaSpec, ...] = (
    TablaSpec(
        origen="prestadores",
        modelo=LiquidacionPrestadorModel,
        columnas=(
            "nombre", "nombre_corto", "cuit", "region", "activo", "created_at", "updated_at",
        ),
        bools=("activo",),
        bool_defaults={"activo": True},
        timestamps=("created_at", "updated_at"),
    ),
    TablaSpec(
        origen="spsts",
        modelo=SpstModel,
        columnas=(
            "prestador_id", "nombre", "domicilio", "localidad", "provincia", "zona",
            "activo", "created_at",
        ),
        fks={"prestador_id": "prestadores"},
        bools=("activo",),
        bool_defaults={"activo": True},
        timestamps=("created_at",),
    ),
    TablaSpec(
        origen="tarifarios",
        modelo=TarifarioModel,
        columnas=(
            "prestador_id", "tipo_servicio", "zona", "costo_servicio", "costo_km",
            "vigencia_desde", "vigencia_hasta", "created_at",
        ),
        fks={"prestador_id": "prestadores"},
        fechas=("vigencia_desde", "vigencia_hasta"),
        timestamps=("created_at",),
    ),
    TablaSpec(
        origen="tabla_kms",
        modelo=TablaKmModel,
        columnas=(
            "prestador_id", "spst_id", "empresa_nombre", "sucursal_nombre", "observaciones",
            "domicilio_cliente", "localidad_cliente", "provincia_cliente", "kms_recorrido",
            "umbral_viatico", "aplica_viatico", "kms_a_facturar", "url_maps",
            "created_at", "updated_at",
        ),
        fks={"prestador_id": "prestadores", "spst_id": "spsts"},
        bools=("aplica_viatico",),
        bool_defaults={"aplica_viatico": False},
        timestamps=("created_at", "updated_at"),
    ),
    TablaSpec(
        origen="liquidaciones",
        modelo=LiquidacionModel,
        columnas=(
            "prestador_id", "numero_liquidacion", "periodo", "tipo_liquidacion",
            "nombre_archivo", "fecha_importacion", "estado", "total_incidentes",
            "total_alertas", "total_importe",
        ),
        fks={"prestador_id": "prestadores"},
        timestamps=("fecha_importacion",),
    ),
    TablaSpec(
        origen="incidentes",
        modelo=IncidenteModel,
        columnas=(
            "liquidacion_id", "numero_incidente", "rubro", "tipo", "empresa_nombre",
            "sucursal_nombre", "nro_serie", "fecha_cierre", "costo_servicio_cobrado",
            "cant_km_cobrado", "costo_km_cobrado", "total_viaje_cobrado",
            "costo_total_cobrado", "pasa_it", "costo_servicio_esperado",
            "cant_km_esperado", "costo_km_esperado", "estado_validacion",
        ),
        fks={"liquidacion_id": "liquidaciones"},
        bools=("pasa_it",),
        bool_defaults={"pasa_it": True},
        fechas=("fecha_cierre",),
    ),
    TablaSpec(
        origen="alertas",
        modelo=AlertaModel,
        columnas=(
            "incidente_id", "liquidacion_id", "tipo_alerta", "descripcion",
            "datos_contexto", "riesgo", "estado", "fecha_generacion",
        ),
        fks={"incidente_id": "incidentes", "liquidacion_id": "liquidaciones"},
        jsons=("datos_contexto",),
        timestamps=("fecha_generacion",),
        post_procesar=_remap_ids_en_contexto_alerta,
    ),
    TablaSpec(
        origen="resoluciones",
        modelo=ResolucionModel,
        columnas=("alerta_id", "decision", "justificacion", "comentario", "fecha"),
        fks={"alerta_id": "alertas"},
        timestamps=("fecha",),
    ),
    # `observaciones`/`observacion_incidentes` (legacy SQLite) ya no tienen tabla
    # destino: se unificaron en `alertas`/`alerta_incidentes` (ver migración
    # b7e4d9a2c531). Esta migración de datos legacy ya corrió una sola vez en
    # 2026-08-21, antes de esa unificación — no vuelve a correr.
)
