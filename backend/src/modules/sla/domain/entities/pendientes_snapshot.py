from dataclasses import dataclass
from datetime import datetime

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar


@dataclass(frozen=True, slots=True)
class PrestadorPendientes:
    """Conteo de incidentes sin cerrar para un PST específico."""

    id_tecnico: int
    tecnico: str
    cantidad: int
    ids_incidente: list[int]


@dataclass(frozen=True, slots=True)
class PendientesSnapshot:
    """Resultado de la última consulta a Siges ya agregado y persistido —
    no tiene dimensión de período porque el backlog de 'sin cerrar' es
    transversal a todos los meses."""

    total: int
    incidentes: list[IncidenteSinCerrar]
    por_prestador: list[PrestadorPendientes]
    updated_at: datetime
