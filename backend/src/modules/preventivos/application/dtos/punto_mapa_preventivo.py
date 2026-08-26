from dataclasses import dataclass
from datetime import date, datetime

from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)


@dataclass(frozen=True, slots=True)
class ConteoEstado:
    """Cuántos equipos de una sucursal están en un estado dado — permite
    mostrar el desglose real en vez de esconderlo detrás de `peor_estado`."""

    estado: EstadoPreventivo
    cantidad: int


@dataclass(frozen=True, slots=True)
class PuntoMapaPreventivo:
    """Una sucursal (no una máquina) para el mapa: `peor_estado` decide el
    color del pin (criterio de `ORDEN_ESTADO_PRIORIDAD`), `distribucion` es
    el conteo por estado para no esconder que el peor puede ser un solo
    equipo aislado entre varios al día. `fecha_vencido_min`/`fecha_tentativa_min`
    son la fecha real más urgente de los equipos `vencido`/`sin_preventivo`
    del grupo respectivamente — el popup del mapa prefiere mostrar la fecha
    real ("preventivo sugerido") a un conteo de días."""

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
    fecha_vencido_min: date | None
    fecha_tentativa_min: date | None
    distribucion: tuple[ConteoEstado, ...]


@dataclass(frozen=True, slots=True)
class ListPuntosMapaResult:
    puntos: list[PuntoMapaPreventivo]
    consultado_en: datetime
