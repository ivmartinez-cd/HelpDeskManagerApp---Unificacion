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
class LiquidacionDetalle:
    liquidacion: Liquidacion
    incidentes: list[IncidenteDetalle]
    alertas: list[Alerta]
