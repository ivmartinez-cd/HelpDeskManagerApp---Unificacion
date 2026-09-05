from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoxplotParqueDto:
    """Distribución del parque de referencia usado en la estimación —
    solo para el gráfico del panel de candidatos (detectar outliers)."""

    minimo: float
    q1: float
    mediana: float
    q3: float
    maximo: float
    valor_equipo: float
