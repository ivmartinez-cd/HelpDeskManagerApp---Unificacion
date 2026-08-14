from datetime import UTC, datetime

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.domain.entities.pendientes_snapshot import (
    OperadorPendientes,
    PendientesSnapshot,
    PrestadorPendientes,
)
from src.modules.sla.domain.repositories.pendientes_query_gateway import PendientesQueryGateway
from src.modules.sla.domain.repositories.pendientes_snapshot_repository import (
    PendientesSnapshotRepository,
)
from src.modules.sla.domain.repositories.prestador_lookup import PrestadorLookup


def _build_snapshot(
    incidentes: list[IncidenteSinCerrar],
    pst_to_operador: dict[int, str],
    updated_at: datetime,
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
                operador_nombre=pst_to_operador.get(id_tecnico),
            )
            for id_tecnico, grupo in agrupados.items()
        ],
        key=lambda p: p.tecnico,
    )

    conteo_operador: dict[str, int] = {}
    for p in por_prestador:
        if p.operador_nombre:
            prev = conteo_operador.get(p.operador_nombre, 0)
            conteo_operador[p.operador_nombre] = prev + p.cantidad

    por_operador = sorted(
        [OperadorPendientes(operador_nombre=n, cantidad=c) for n, c in conteo_operador.items()],
        key=lambda o: o.operador_nombre,
    )

    return PendientesSnapshot(
        total=len(incidentes),
        incidentes=incidentes,
        por_prestador=por_prestador,
        por_operador=por_operador,
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
        pst_lookup: PrestadorLookup,
        meses_corte: int,
    ) -> None:
        self._gateway = gateway
        self._repo = repo
        self._pst_lookup = pst_lookup
        self._meses_corte = meses_corte

    async def execute(self) -> PendientesSnapshot:
        pst_ids = set(await self._pst_lookup.get_all_pst_siges_ids())
        pst_to_operador = await self._pst_lookup.get_pst_to_operador_mapping()
        todos = await self._gateway.find_incidentes_sin_cerrar(self._meses_corte)
        incidentes = [i for i in todos if i.id_tecnico in pst_ids]
        snapshot = _build_snapshot(incidentes, pst_to_operador, datetime.now(UTC))
        await self._repo.upsert(snapshot)
        return snapshot
