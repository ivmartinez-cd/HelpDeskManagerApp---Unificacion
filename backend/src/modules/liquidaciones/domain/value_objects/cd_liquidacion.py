"""Value objects del SOAP de Canal Directo para liquidaciones."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CdLiquidacion:
    id: int
    prestador_cd_id: int
    numero_liquidacion: str   # f"{id}-{dv}" — dv de numeracion_ayc (pesos 3-1-3-1)
    fecha_liquidacion: date
    estado: str
    cant_incidentes: int
    # id numérico de AyC (1=Preliquidada..5=Cerrada) — el mismo que espera
    # setLiquidationStatus. None si el JSON no lo trae; `estado` (nombre) es el
    # fallback. Ver domain/services/estados_ayc.py.
    estado_id: int | None = None


@dataclass(frozen=True)
class CdLiquidacionDetalle:
    """Detalle adicional de la liquidación que solo viaja en `getLiquidationById`,
    no en `getTopLiquidations`: ítem extra (seguros, documentación, ajustes) y
    número de factura del prestador. Cada campo es independiente — puede haber
    factura sin extra, o extra sin factura todavía (liquidación aún no
    facturada: `FacturaNro=""`). `monto_extra=None`/`concepto_extra=None` es
    "sin extra cargado" (AyC reporta `Extra="0"`), no cero."""

    concepto_extra: str | None
    monto_extra: float | None
    numero_factura: str | None


@dataclass(frozen=True)
class CdIncidenteRow:
    id: int
    tipo: str
    empresa_nombre: str
    sucursal_nombre: str
    nro_serie: str
    fecha_cierre: date | None
    costo_servicio: float
    cant_km: float
    costo_km: float
    rubro: str
    pasa_it: bool
