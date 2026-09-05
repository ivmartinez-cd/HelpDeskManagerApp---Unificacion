from dataclasses import dataclass
from datetime import date

from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.domain.errors import RecesoRangoInvalidoError
from src.modules.contadores.domain.ports.recesos_port import RecesosPort


@dataclass(frozen=True, slots=True)
class CrearRecesoRequest:
    id_grupo_economico: int
    id_anexo: int | None
    fecha_desde: date
    fecha_hasta: date
    descripcion: str


class GestionarRecesosProyeccionUseCase:
    def __init__(self, store: RecesosPort) -> None:
        self._store = store

    async def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        return await self._store.listar(id_grupo_economico)

    async def crear(self, request: CrearRecesoRequest) -> RecesoDto:
        # Un receso invertido se persistía y participaba del tablero (F7).
        if request.fecha_desde > request.fecha_hasta:
            raise RecesoRangoInvalidoError()
        return await self._store.crear(
            RecesoDto(
                id=0,
                id_grupo_economico=request.id_grupo_economico,
                id_anexo=request.id_anexo,
                fecha_desde=request.fecha_desde,
                fecha_hasta=request.fecha_hasta,
                descripcion=request.descripcion,
            )
        )

    async def eliminar(self, id_receso: int) -> None:
        await self._store.eliminar(id_receso)
