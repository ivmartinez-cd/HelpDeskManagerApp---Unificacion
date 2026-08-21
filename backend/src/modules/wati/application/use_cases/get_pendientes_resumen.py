from collections import Counter

from src.modules.wati.application.dtos.pendientes_dtos import (
    ConversacionPendienteDto,
    OperadorPendientesDto,
    PendientesResumenDto,
)
from src.modules.wati.application.use_cases.list_pendientes import ListPendientes
from src.modules.wati.domain.repositories.conversacion_repository import (
    ConversacionRepository,
)

SIN_ASIGNAR = "Sin asignar"


def _por_operador(pendientes: list[ConversacionPendienteDto]) -> list[OperadorPendientesDto]:
    conteo = Counter(p.operador_nombre or SIN_ASIGNAR for p in pendientes)
    return [
        OperadorPendientesDto(operador=op, cantidad=n)
        for op, n in sorted(conteo.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


class GetPendientesResumen:
    def __init__(self, repo: ConversacionRepository, list_pendientes: ListPendientes) -> None:
        self._repo = repo
        self._list = list_pendientes

    async def execute(self) -> PendientesResumenDto:
        pendientes = await self._list.execute()
        return PendientesResumenDto(
            total=len(pendientes),
            sin_asignar=sum(1 for p in pendientes if p.sin_asignar),
            max_minutos_esperando=max((p.minutos_esperando for p in pendientes), default=0),
            por_operador=_por_operador(pendientes),
            sincronizado_at=await self._repo.get_ultima_sincronizacion(),
        )
