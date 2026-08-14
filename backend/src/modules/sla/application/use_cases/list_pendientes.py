from src.modules.sla.application.dtos.pendientes_dtos import IncidenteSinCerrarDTO
from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.domain.repositories.pendientes_snapshot_repository import (
    PendientesSnapshotRepository,
)


def _to_dto(inc: IncidenteSinCerrar) -> IncidenteSinCerrarDTO:
    return IncidenteSinCerrarDTO(
        id_incidente=inc.id_incidente,
        tecnico=inc.tecnico,
        id_tecnico=inc.id_tecnico,
        cliente=inc.cliente,
        sucursal=inc.sucursal,
        modelo=inc.modelo,
        nro_serie=inc.nro_serie,
        fecha_ingreso=inc.fecha_ingreso,
        fecha_finalizacion=inc.fecha_finalizacion,
        dias_en_estado=inc.dias_en_estado,
    )


class ListPendientes:
    """Detalle de los incidentes sin cerrar.

    `siges_ids_filtro=None` trae todos; lista vacía devuelve vacío (no ve nada
    si el operador no tiene PST asignados — diverge del criterio de
    ListIncidentesVencidos que convierte [] a None)."""

    def __init__(
        self, repo: PendientesSnapshotRepository, refresher: RefreshPendientesSnapshot
    ) -> None:
        self._repo = repo
        self._refresher = refresher

    async def execute(
        self, *, siges_ids_filtro: list[int] | None = None
    ) -> list[IncidenteSinCerrarDTO]:
        if siges_ids_filtro is not None and len(siges_ids_filtro) == 0:
            return []
        snapshot = await self._repo.get() or await self._refresher.execute()
        incidentes = snapshot.incidentes
        if siges_ids_filtro is not None:
            filtro = set(siges_ids_filtro)
            incidentes = [i for i in incidentes if i.id_tecnico in filtro]
        ordenados = sorted(incidentes, key=lambda i: i.dias_en_estado, reverse=True)
        return [_to_dto(i) for i in ordenados]
