from src.modules.sla.application.dtos.sla_dtos import IncidenteVencidoDTO
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.repositories.sla_snapshot_repository import SlaSnapshotRepository


def _to_dto(incidente: IncidenteSla) -> IncidenteVencidoDTO:
    return IncidenteVencidoDTO(
        id_incidente=incidente.id_incidente,
        tecnico=incidente.tecnico,
        region=incidente.region,
        cliente=incidente.cliente,
        sucursal=incidente.sucursal,
        modelo=incidente.modelo,
        nro_serie=incidente.nro_serie,
        fecha_ingreso=incidente.fecha_ingreso,
        fecha_operativo=incidente.fecha_operativo,
        tiempo=incidente.tiempo,
        rango=incidente.rango,
        sla_horas=incidente.sla_horas,
        horas_vencido=incidente.horas_vencido,
    )


class ListIncidentesVencidos:
    """Detalle de los incidentes vencidos del período — lee el mismo snapshot
    cacheado que GetSlaCompliance (ver RefreshSlaSnapshot)."""

    def __init__(self, repo: SlaSnapshotRepository, refresher: RefreshSlaSnapshot) -> None:
        self._repo = repo
        self._refresher = refresher

    async def execute(self, periodo: int) -> list[IncidenteVencidoDTO]:
        snapshot = await self._repo.get(periodo) or await self._refresher.execute(periodo)
        return [_to_dto(i) for i in snapshot.incidentes_vencidos]
