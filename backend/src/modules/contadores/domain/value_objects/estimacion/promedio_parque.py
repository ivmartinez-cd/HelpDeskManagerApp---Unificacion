from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromedioParque:
    """Valor representativo ya resuelto por la consulta de un nivel de la
    cascada de parque (`Prom` del legacy: mediana truncada P80 con N>=5,
    mediana cruda con N=2..4, NULL con N<=1), más las métricas de auditoría
    del tooltip. `q1`/`q3` solo vienen en el nivel Cliente+Tecnología."""

    valor: float
    n_equipos: int
    n_descartados: int = 0
    mediana_cruda: float | None = None
    media_cruda: float | None = None
    q1: float | None = None
    q3: float | None = None
