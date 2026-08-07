from src.modules.contadores.domain.value_objects.counter_reading import CounterReading

RESET_COUNTER_TYPES = frozenset({"Reiniciar Contador"})


def find_last_reset_index(readings: list[CounterReading]) -> int | None:
    """Índice de la última lectura que marca un reset del contador: ya sea
    explícito (`tipo_contador` en RESET_COUNTER_TYPES) o implícito (el
    contador bajó respecto a la lectura anterior). `None` si no hubo reset."""
    last_reset: int | None = None
    for i, reading in enumerate(readings):
        is_flagged = reading.tipo_contador in RESET_COUNTER_TYPES
        is_drop = i > 0 and reading.contador < readings[i - 1].contador
        if is_flagged or is_drop:
            last_reset = i
    return last_reset
