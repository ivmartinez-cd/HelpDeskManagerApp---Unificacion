from src.modules.sla.application.dtos.pendientes_dtos import (
    OperadorPendientesDTO,
    PendientesResumenResult,
    PrestadorPendientesDTO,
)
from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.domain.repositories.pendientes_snapshot_repository import (
    PendientesSnapshotRepository,
)


class GetPendientesResumen:
    """Conteo de incidentes sin cerrar por prestador — lee el snapshot
    cacheado; si no hay uno todavía (cold start), dispara un refresh en vivo."""

    def __init__(
        self, repo: PendientesSnapshotRepository, refresher: RefreshPendientesSnapshot
    ) -> None:
        self._repo = repo
        self._refresher = refresher

    async def execute(
        self, *, siges_ids_filtro: list[int] | None = None
    ) -> PendientesResumenResult:
        snapshot = await self._repo.get() or await self._refresher.execute()
        por_prestador = snapshot.por_prestador
        if siges_ids_filtro is not None:
            filtro = set(siges_ids_filtro)
            por_prestador = [p for p in por_prestador if p.id_tecnico in filtro]
        total = sum(p.cantidad for p in por_prestador)
        conteo_op: dict[str, int] = {}
        for p in por_prestador:
            if p.operador_nombre:
                conteo_op[p.operador_nombre] = conteo_op.get(p.operador_nombre, 0) + p.cantidad
        por_operador = sorted(
            [OperadorPendientesDTO(operador_nombre=n, cantidad=c) for n, c in conteo_op.items()],
            key=lambda o: o.operador_nombre,
        )
        return PendientesResumenResult(
            total=total,
            por_prestador=[
                PrestadorPendientesDTO(
                    id_tecnico=p.id_tecnico,
                    tecnico=p.tecnico,
                    cantidad=p.cantidad,
                    ids_incidente=p.ids_incidente,
                    operador_nombre=p.operador_nombre,
                )
                for p in por_prestador
            ],
            por_operador=por_operador,
            updated_at=snapshot.updated_at,
        )
