"""DTO de salida de GetLiquidacionDetalle."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion


@dataclass(frozen=True)
class IncidenteDetalle:
    """Incidente + datos de la fila de tabla KM que matchea por sucursal (port del
    enriquecimiento que el legacy hacía en GET /liquidaciones/{id})."""

    incidente: Incidente
    localidad_cliente: str | None
    spst_id: UUID | None
    url_maps: str | None


@dataclass(frozen=True)
class CotizacionUsdDetalle:
    """Dólar oficial del período de la liquidación — `None` si el período es
    anterior a 2026-01 o todavía no se sincronizó (switch ARS/USD del
    frontend queda deshabilitado en ese caso)."""

    compra: float
    venta: float


@dataclass(frozen=True)
class LiquidacionDetalle:
    liquidacion: Liquidacion
    incidentes: list[IncidenteDetalle]
    alertas: list[Alerta]
    cotizacion_usd: CotizacionUsdDetalle | None
