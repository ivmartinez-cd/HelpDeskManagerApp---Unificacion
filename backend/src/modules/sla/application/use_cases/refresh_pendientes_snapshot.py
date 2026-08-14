from datetime import UTC, datetime

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.domain.entities.pendientes_snapshot import (
    PendientesSnapshot,
    PrestadorPendientes,
)
from src.modules.sla.domain.repositories.pendientes_query_gateway import PendientesQueryGateway
from src.modules.sla.domain.repositories.pendientes_snapshot_repository import (
    PendientesSnapshotRepository,
)


def _build_snapshot(
    incidentes: list[IncidenteSinCerrar], updated_at: datetime
) -> PendientesSnapshot:
    agrupados: dict[int, list[IncidenteSinCerrar]] = {}
    for inc in incidentes:
        agrupados.setdefault(inc.id_tecnico, []).append(inc)

    por_prestador = sorted(
        [
            PrestadorPendientes(
                id_tecnico=id_tecnico,
                tecnico=grupo[0].tecnico,
                cantidad=len(grupo),
                ids_incidente=[i.id_incidente for i in grupo],
            )
            for id_tecnico, grupo in agrupados.items()
        ],
        key=lambda p: p.tecnico,
    )
    return PendientesSnapshot(
        total=len(incidentes),
        incidentes=incidentes,
        por_prestador=por_prestador,
        updated_at=updated_at,
    )


class RefreshPendientesSnapshot:
    """Único caso de uso que consulta Siges en vivo para el backlog de
    incidentes sin cerrar — lo dispara el botón 'Actualizar', el job de
    fondo periódico, o un cold start."""

    def __init__(
        self,
        gateway: PendientesQueryGateway,
        repo: PendientesSnapshotRepository,
        meses_corte: int,
    ) -> None:
        self._gateway = gateway
        self._repo = repo
        self._meses_corte = meses_corte

    async def execute(self) -> PendientesSnapshot:
        incidentes = await self._gateway.find_incidentes_sin_cerrar(self._meses_corte)
        snapshot = _build_snapshot(incidentes, datetime.now(UTC))
        await self._repo.upsert(snapshot)
        return snapshot
