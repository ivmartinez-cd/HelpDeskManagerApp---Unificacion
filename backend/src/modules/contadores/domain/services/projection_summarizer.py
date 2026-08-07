from statistics import median

from src.modules.contadores.domain.value_objects.counter_projection_result import (
    CounterProjectionResult,
)
from src.modules.contadores.domain.value_objects.projection_summary import (
    DISTRIBUTION_LABELS,
    ProjectionSummary,
)

_DISTRIBUTION_BOUNDS = (1, 7, 30, 90, 365)


def summarize(results: list[CounterProjectionResult]) -> ProjectionSummary:
    proyectados = [r for r in results if r.metodo == "PROYECTADO"]
    dias = [r.dias_proyectados for r in proyectados if r.dias_proyectados is not None]
    consumos = [
        r.consumo_diario_promedio
        for r in proyectados
        if r.consumo_diario_promedio and r.consumo_diario_promedio > 0
    ]
    return ProjectionSummary(
        total=len(results),
        reales=sum(1 for r in results if r.metodo == "REAL"),
        proyectados=len(proyectados),
        sin_datos=sum(1 for r in results if r.metodo == "SIN_DATOS"),
        dias_mediana=median(dias) if dias else 0.0,
        dias_max=max(dias) if dias else 0,
        consumo_mediana=median(consumos) if consumos else 0.0,
        consumo_max=max(consumos) if consumos else 0.0,
        distribucion_dias=_distribution(dias),
    )


def _distribution(dias: list[int]) -> dict[str, int]:
    counts = dict.fromkeys(DISTRIBUTION_LABELS, 0)
    for d in dias:
        counts[_bucket_label(d)] += 1
    return counts


def _bucket_label(dias: int) -> str:
    for bound, label in zip(_DISTRIBUTION_BOUNDS, DISTRIBUTION_LABELS, strict=False):
        if dias <= bound:
            return label
    return DISTRIBUTION_LABELS[-1]
