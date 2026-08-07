from dataclasses import dataclass
from datetime import timedelta

from src.modules.contadores.domain.services.reset_detector import find_last_reset_index
from src.modules.contadores.domain.value_objects.counter_reading import CounterReading
from src.modules.contadores.domain.value_objects.projection_settings import ProjectionSettings


@dataclass(frozen=True, slots=True)
class TrendWindow:
    readings: list[CounterReading]
    reset_index: int | None
    used_recent_window: bool


def select_trend_window(
    historical: list[CounterReading], settings: ProjectionSettings
) -> TrendWindow:
    """Qué lecturas históricas usar para calcular la tendencia de consumo:
    desde el último reset (si hubo), y dentro de eso, priorizando una
    ventana reciente si tiene >=2 lecturas propias."""
    reset_index = find_last_reset_index(historical)
    valid = historical[reset_index:] if reset_index is not None else historical

    limite_reciente = valid[-1].fecha - timedelta(days=settings.ventana_reciente_dias)
    recientes = [r for r in valid if r.fecha >= limite_reciente]

    if len(recientes) >= 2:
        return TrendWindow(recientes, reset_index, used_recent_window=True)
    return TrendWindow(valid, reset_index, used_recent_window=False)
