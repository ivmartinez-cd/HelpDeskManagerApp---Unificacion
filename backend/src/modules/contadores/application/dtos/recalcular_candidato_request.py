from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RecalcularCandidatoRequest:
    id_maquina: int
    clase: str
    partida_fecha: date
    partida_valor: float
    partida_tipo_toma: int
    llegada_fecha: date
    llegada_valor: float
    llegada_tipo_toma: int
    # Presentes solo cuando `clase` es un equipo real de Siges (fallback del
    # router si el modo ejemplo no lo encuentra) — identifican qué grilla ya
    # cargada en caché reusar (ver PyodbcGrillaEstimacionGateway._CACHE_TTL).
    nro_proceso: int | None = None
    id_grupo_economico: int | None = None
    id_anexo: int | None = None
    fecha_objetivo: date | None = None
