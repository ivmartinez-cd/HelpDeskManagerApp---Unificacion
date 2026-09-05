from dataclasses import dataclass
from datetime import date
from typing import Literal

MetodoForzado = Literal["entre_reales", "cascada_parque"]


@dataclass(frozen=True, slots=True)
class ForzarMetodoRequest:
    id_maquina: int
    clase: str
    metodo: MetodoForzado
    # Presentes solo para un equipo real de Siges — mismo criterio que
    # RecalcularCandidatoRequest (identifican qué grilla cacheada reusar).
    nro_proceso: int | None = None
    id_grupo_economico: int | None = None
    id_anexo: int | None = None
    fecha_objetivo: date | None = None
