from datetime import UTC, datetime

from src.modules.sla.domain.entities.sla_snapshot import SlaSnapshot
from src.modules.sla.domain.repositories.sla_query_gateway import SlaQueryGateway
from src.modules.sla.domain.repositories.sla_snapshot_repository import SlaSnapshotRepository
from src.modules.sla.domain.services.sla_compliance import build_snapshot
from src.modules.sla.domain.value_objects.periodo import Periodo


class RefreshSlaSnapshot:
    """Único caso de uso que pega en vivo contra Siges/MERCURIO — lo dispara
    el botón "Actualizar", el job de fondo periódico, o un cache-miss de
    GetSlaCompliance/ListIncidentesVencidos. Siempre persiste lo que trae."""

    def __init__(self, gateway: SlaQueryGateway, repo: SlaSnapshotRepository) -> None:
        self._gateway = gateway
        self._repo = repo

    async def execute(self, periodo: int) -> SlaSnapshot:
        incidentes = await self._gateway.find_incidentes(Periodo(periodo))
        snapshot = build_snapshot(periodo, incidentes, datetime.now(UTC))
        await self._repo.upsert(snapshot)
        return snapshot
