from dataclasses import dataclass
from datetime import datetime

from src.modules.sla.domain.entities.incidente_sla import IncidenteSla


@dataclass(frozen=True, slots=True)
class TecnicoVencidos:
    """Un grupo del desglose de vencidos por técnico/PST."""

    tecnico: str
    cantidad: int
    ids_incidente: list[int]


@dataclass(frozen=True, slots=True)
class SlaSnapshot:
    """Resultado de una consulta a Siges/MERCURIO ya agregado y persistido —
    lo que RefreshSlaSnapshot guarda y lo que las lecturas (GetSlaCompliance,
    ListIncidentesVencidos) devuelven mientras no haya un refresh más nuevo."""

    periodo: int
    total: int
    correctos: int
    vencidos: int
    pct_correctos: float
    pct_vencidos: float
    vencidos_por_tecnico: list[TecnicoVencidos]
    incidentes_vencidos: list[IncidenteSla]
    updated_at: datetime
