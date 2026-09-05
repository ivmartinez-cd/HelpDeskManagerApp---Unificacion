from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class SolicitudRecalculoSigesDto:
    """Lo que el frontend ya tiene tras elegir Grupo económico → Proceso —
    identifica qué grilla cacheada reusar (agrupado, ARCHITECTURE_GUIDE.md
    §4). Compartido por `RecalcularCandidatoSigesUseCase` y
    `ForzarMetodoCandidatoSigesUseCase` (vía `ConstructorEntradaSiges`)."""

    nro_proceso: int
    id_grupo_economico: int
    id_anexo: int
    fecha_objetivo: date
