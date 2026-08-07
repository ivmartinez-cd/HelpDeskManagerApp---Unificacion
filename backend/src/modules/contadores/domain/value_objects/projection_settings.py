from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectionSettings:
    """Parámetros ajustables del algoritmo de proyección — agrupados en un
    objeto en vez de 5 parámetros sueltos (ARCHITECTURE_GUIDE.md §4)."""

    tolerancia_dias: int = 2
    min_dias_intervalo: int = 1
    ventana_reciente_dias: int = 365
    umbral_minimo_consumo: float = 0.2
    max_antiguedad_lectura_dias: int = 365
