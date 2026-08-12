"""Resultado de parsear el archivo de preliquidación de un prestador — previo a
persistir (`IncidenteImportado` no tiene `id`/`liquidacion_id` todavía, a diferencia
de la entidad `Incidente`)."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class IncidenteImportado:
    numero_incidente: str
    rubro: str
    tipo: str
    empresa_nombre: str
    sucursal_nombre: str
    nro_serie: str
    fecha_cierre: date | None
    costo_servicio_cobrado: float
    cant_km_cobrado: float
    costo_km_cobrado: float
    total_viaje_cobrado: float
    costo_total_cobrado: float
    pasa_it: bool


@dataclass(frozen=True)
class ResultadoImportacion:
    """`numero_liquidacion`/`periodo` son `""` (no `None`) cuando no se pudieron
    extraer del nombre de archivo/fechas — mismo comportamiento que el legacy, que
    guardaba la cadena vacía tal cual en la tabla."""

    numero_liquidacion: str
    periodo: str
    tipo_liquidacion: str
    incidentes: list[IncidenteImportado]
