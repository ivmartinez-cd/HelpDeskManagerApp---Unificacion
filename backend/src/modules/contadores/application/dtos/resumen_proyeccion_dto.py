from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ResumenProyeccionDto:
    """KPIs del tablero, mismo criterio que `GrillaEstimacion` del legacy:
    `estimados` son las filas a estimar que no quedaron pendientes
    (`PendienteEstimar && !RequierePendiente`), `total` las máquinas
    distintas (no las filas)."""

    reales: int
    estimados: int
    pendientes: int
    sospechosos: int
    total: int


@dataclass(frozen=True, slots=True)
class RestauracionDecisionesDto:
    """Banner "Restauramos N decisiones de una sesión anterior (M
    descartadas)" del legacy. `vigentes_hasta` es la última decisión guardada
    del proceso: lo que el frontend manda como `descartar_hasta` cuando el
    operador aprieta "Descartar y empezar limpio"."""

    restauradas: int = 0
    descartadas: int = 0
    vigentes_hasta: datetime | None = None
