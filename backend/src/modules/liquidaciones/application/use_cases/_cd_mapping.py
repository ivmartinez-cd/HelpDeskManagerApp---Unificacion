"""Traducción SOAP→dominio compartida por `sincronizar_liquidaciones.py` (crear
liquidaciones nuevas) y `_reconciliar_liquidacion.py` (actualizar incidentes de
liquidaciones ya existentes) — antes vivía duplicada/inline solo en el primero."""

from src.modules.liquidaciones.domain.services.importacion.normalizacion import (
    normalizar_tipo_servicio,
)
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdIncidenteRow,
    CdLiquidacion,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import IncidenteImportado


def a_importado(row: CdIncidenteRow) -> IncidenteImportado:
    total_viaje = round(row.cant_km * row.costo_km, 2)
    return IncidenteImportado(
        numero_incidente=str(row.id),
        rubro=row.rubro or "Impresoras",
        tipo=normalizar_tipo_servicio(row.tipo),
        empresa_nombre=row.empresa_nombre,
        sucursal_nombre=row.sucursal_nombre,
        nro_serie=row.nro_serie,
        fecha_cierre=row.fecha_cierre,
        costo_servicio_cobrado=row.costo_servicio,
        cant_km_cobrado=row.cant_km,
        costo_km_cobrado=row.costo_km,
        total_viaje_cobrado=total_viaje,
        costo_total_cobrado=round(row.costo_servicio + total_viaje, 2),
        pasa_it=row.pasa_it,
    )


def periodo_desde_fecha(cd_liq: CdLiquidacion) -> str:
    f = cd_liq.fecha_liquidacion
    if f.month == 1:
        return f"{f.year - 1}-12"
    return f"{f.year}-{f.month - 1:02d}"
