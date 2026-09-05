from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromedioParque:
    """Valor representativo ya resuelto de un nivel de la cascada de parque
    (REGLAS_DE_NEGOCIO §5.5), más las métricas de auditoría que necesita el
    detalle de observación (§12). `q1`/`q3` solo aplican al nivel
    Cliente+Tecnología cuando se aplicó el criterio IQR."""

    valor: float
    n_equipos: int
    n_descartados: int = 0
    mediana_cruda: float | None = None
    media_cruda: float | None = None
    q1: float | None = None
    q3: float | None = None
