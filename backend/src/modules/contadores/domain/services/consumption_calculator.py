from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.counter_reading import CounterReading
from src.modules.contadores.domain.value_objects.projection_settings import ProjectionSettings


@dataclass(frozen=True, slots=True)
class ConsumptionOutcome:
    consumo_diario: float
    descripcion: str
    notas: list[str]


def calculate_daily_consumption(
    readings: list[CounterReading], settings: ProjectionSettings
) -> ConsumptionOutcome:
    """Promedio de páginas/día entre lecturas consecutivas válidas. Un
    intervalo se descarta si el contador bajó (reset) o si la diferencia de
    días es menor al mínimo configurado."""
    if len(readings) < 2:
        return ConsumptionOutcome(0.0, "Una sola lectura — sin tendencia calculable", [])

    deltas, notas = _valid_interval_deltas(readings, settings.min_dias_intervalo)
    if not deltas:
        return ConsumptionOutcome(
            0.0, "Sin intervalos validos (todos negativos o mismo dia)", notas
        )

    consumo = sum(deltas) / len(deltas)
    if consumo <= settings.umbral_minimo_consumo:
        notas.append(
            f"Consumo promedio ({consumo:.4f}) <= umbral ({settings.umbral_minimo_consumo}) -> 0.0"
        )
        return ConsumptionOutcome(
            0.0, f"Consumo por debajo del umbral de {settings.umbral_minimo_consumo}", notas
        )

    return ConsumptionOutcome(consumo, f"Promedio de {len(deltas)} intervalo(s) valido(s)", notas)


def _valid_interval_deltas(
    readings: list[CounterReading], min_dias_intervalo: int
) -> tuple[list[float], list[str]]:
    deltas: list[float] = []
    notas: list[str] = []
    for prev, curr in zip(readings, readings[1:], strict=False):
        dias = (curr.fecha - prev.fecha).days
        diff = curr.contador - prev.contador
        if dias < min_dias_intervalo:
            notas.append(f"Intervalo {prev.fecha}->{curr.fecha}: {dias}d — omitido (mismo dia)")
            continue
        if diff < 0:
            notas.append(f"Intervalo {prev.fecha}->{curr.fecha}: diff={diff} — omitido (reset)")
            continue
        deltas.append(diff / dias)
    return deltas, notas
