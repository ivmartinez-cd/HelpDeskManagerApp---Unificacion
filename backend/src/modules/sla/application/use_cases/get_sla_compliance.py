from collections import defaultdict

from src.modules.sla.application.dtos.sla_dtos import (
    GetSlaComplianceRequest,
    SlaComplianceResult,
    TecnicoVencidosDTO,
)
from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.repositories.sla_query_gateway import SlaQueryGateway
from src.modules.sla.domain.value_objects.periodo import Periodo


def _pct(parte: int, total: int) -> float:
    return round(parte * 100 / total, 2) if total else 0.0


def _agrupar_por_tecnico(vencidos: list[IncidenteSla]) -> list[TecnicoVencidosDTO]:
    ids_por_tecnico: dict[str, list[int]] = defaultdict(list)
    for incidente in vencidos:
        ids_por_tecnico[incidente.tecnico].append(incidente.id_incidente)
    grupos = [
        TecnicoVencidosDTO(tecnico=tecnico, cantidad=len(ids), ids_incidente=ids)
        for tecnico, ids in ids_por_tecnico.items()
    ]
    return sorted(grupos, key=lambda g: (-g.cantidad, g.tecnico))


class GetSlaCompliance:
    """Caso de uso: resumen Correcto/Vencido del período + desglose de vencidos
    por técnico/PST — la misma cuenta que la tabla dinámica de Excel manual."""

    def __init__(self, gateway: SlaQueryGateway) -> None:
        self._gateway = gateway

    async def execute(self, request: GetSlaComplianceRequest) -> SlaComplianceResult:
        incidentes = await self._gateway.find_incidentes(Periodo(request.periodo))
        vencidos = [i for i in incidentes if i.es_vencido]
        total, cant_vencidos = len(incidentes), len(vencidos)
        return SlaComplianceResult(
            periodo=request.periodo,
            total=total,
            correctos=total - cant_vencidos,
            vencidos=cant_vencidos,
            pct_correctos=_pct(total - cant_vencidos, total),
            pct_vencidos=_pct(cant_vencidos, total),
            vencidos_por_tecnico=_agrupar_por_tecnico(vencidos),
        )
