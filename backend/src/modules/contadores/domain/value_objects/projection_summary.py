from dataclasses import dataclass, field

DISTRIBUTION_LABELS = ("1 dia", "2-7 dias", "8-30 dias", "31-90 dias", "91-365 dias", "+365 dias")


@dataclass(frozen=True, slots=True)
class ProjectionSummary:
    """KPIs de una corrida completa de proyección — alimenta la hoja "KPIs"
    del Excel y el dashboard del frontend. `distribucion_dias` usa las claves
    de `DISTRIBUTION_LABELS`, en ese orden."""

    total: int
    reales: int
    proyectados: int
    sin_datos: int
    dias_mediana: float
    dias_max: int
    consumo_mediana: float
    consumo_max: float
    distribucion_dias: dict[str, int] = field(default_factory=dict)
