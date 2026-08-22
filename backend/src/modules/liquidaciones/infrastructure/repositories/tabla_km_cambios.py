"""`CambiosTablaKm`: el tipo con el que `SqlAlchemyTablaKmRepository` expresa sus
escrituras parciales sobre `tabla_kms` (un subconjunto de columnas; `total=False`
permite armarlo por partes y mypy valida nombre y tipo de cada clave contra las
columnas del modelo), más los helpers que lo aplican sobre la fila ORM."""

import uuid
from datetime import datetime
from typing import TypedDict

from src.modules.liquidaciones.infrastructure.models.tabla_km_model import TablaKmModel


class CambiosTablaKm(TypedDict, total=False):
    prestador_id: uuid.UUID
    spst_id: uuid.UUID | None
    empresa_nombre: str
    sucursal_nombre: str
    observaciones: str | None
    domicilio_cliente: str | None
    localidad_cliente: str | None
    provincia_cliente: str | None
    kms_recorrido: float
    umbral_viatico: float
    aplica_viatico: bool
    kms_a_facturar: float
    url_maps: str | None
    latitud_destino: float | None
    longitud_destino: float | None
    kms_ida: float | None
    kms_vuelta: float | None
    coords_origen: str | None
    geocode_formatted_address: str | None
    geocode_fecha: datetime | None
    siges_sucursal_id: int | None
    id_costo_servicios: int | None
    updated_at: datetime


def vinculo_siges_si_presente(
    siges_sucursal_id: int | None, id_costo_servicios: int | None
) -> CambiosTablaKm:
    """`update_distancias`/`update_domicilio` solo pisan el vínculo Siges cuando
    el caller lo manda; con None la fila conserva el que ya tenía."""
    cambios: CambiosTablaKm = {}
    if siges_sucursal_id is not None:
        cambios["siges_sucursal_id"] = siges_sucursal_id
    if id_costo_servicios is not None:
        cambios["id_costo_servicios"] = id_costo_servicios
    return cambios


def aplicar_cambios(row: TablaKmModel, cambios: CambiosTablaKm) -> None:
    for campo, valor in cambios.items():
        setattr(row, campo, valor)
