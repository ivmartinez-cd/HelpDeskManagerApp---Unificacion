from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResumenProyeccionDto:
    """KPIs del tablero (§ KPIs del brief de UI)."""

    reales: int
    estimados: int
    pendientes: int
    sospechosos: int
    total: int
