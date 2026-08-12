from src.modules.sla.application.dtos.sla_dtos import (
    GetSlaComplianceRequest,
    SlaComplianceResult,
    TecnicoVencidosDTO,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.domain.repositories.sla_snapshot_repository import SlaSnapshotRepository


class GetSlaCompliance:
    """Resumen Correcto/Vencido del período — lee el snapshot cacheado; si
    todavía no hay uno guardado para ese período (cold start), dispara un
    refresh en vivo una sola vez y lo persiste para las próximas lecturas."""

    def __init__(self, repo: SlaSnapshotRepository, refresher: RefreshSlaSnapshot) -> None:
        self._repo = repo
        self._refresher = refresher

    async def execute(self, request: GetSlaComplianceRequest) -> SlaComplianceResult:
        snapshot = await self._repo.get(request.periodo) or await self._refresher.execute(
            request.periodo
        )
        return SlaComplianceResult(
            periodo=snapshot.periodo,
            total=snapshot.total,
            correctos=snapshot.correctos,
            vencidos=snapshot.vencidos,
            pct_correctos=snapshot.pct_correctos,
            pct_vencidos=snapshot.pct_vencidos,
            vencidos_por_tecnico=[
                TecnicoVencidosDTO(
                    tecnico=t.tecnico,
                    id_tecnico=t.id_tecnico,
                    cantidad=t.cantidad,
                    ids_incidente=t.ids_incidente,
                )
                for t in snapshot.vencidos_por_tecnico
            ],
            updated_at=snapshot.updated_at,
        )
