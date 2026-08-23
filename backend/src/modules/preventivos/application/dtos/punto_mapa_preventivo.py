from dataclasses import dataclass
from datetime import datetime

from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)


@dataclass(frozen=True, slots=True)
class PuntoMapaPreventivo:
    """Una sucursal (no una máquina) para el mapa: colapsa todo su parque en
    el estado más urgente, con el criterio de `ORDEN_ESTADO_PRIORIDAD`."""

    id_sucursal: int
    cliente: str
    sucursal: str
    zona: str
    domicilio: str
    latitud: float | None
    longitud: float | None
    ubicado: bool
    cant_maquinas: int
    cant_habilitadas: int
    peor_estado: EstadoPreventivo
    dias_vencido_max: int | None


@dataclass(frozen=True, slots=True)
class ListPuntosMapaResult:
    puntos: list[PuntoMapaPreventivo]
    consultado_en: datetime
