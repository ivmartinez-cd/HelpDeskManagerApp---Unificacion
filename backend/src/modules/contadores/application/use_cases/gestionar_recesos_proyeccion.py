from dataclasses import dataclass
from datetime import date

from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.infrastructure.ejemplo.recesos_store import RecesosEjemploStore


@dataclass(frozen=True, slots=True)
class CrearRecesoRequest:
    id_grupo_economico: int
    id_anexo: int | None
    fecha_desde: date
    fecha_hasta: date
    descripcion: str


class GestionarRecesosProyeccionUseCase:
    def __init__(self, store: RecesosEjemploStore) -> None:
        self._store = store

    def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        return self._store.listar(id_grupo_economico)

    def crear(self, request: CrearRecesoRequest) -> RecesoDto:
        return self._store.crear(
            RecesoDto(
                id=0,
                id_grupo_economico=request.id_grupo_economico,
                id_anexo=request.id_anexo,
                fecha_desde=request.fecha_desde,
                fecha_hasta=request.fecha_hasta,
                descripcion=request.descripcion,
            )
        )

    def eliminar(self, id_receso: int) -> None:
        self._store.eliminar(id_receso)
