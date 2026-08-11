from dataclasses import dataclass

from src.modules.turnos.application.dtos.turno_dtos import CasillaDTO
from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository


@dataclass(frozen=True, slots=True)
class ListCasillasDependencies:
    casillas: CasillaRepository


class ListCasillas:
    """Caso de uso: lista las casillas configuradas."""

    def __init__(self, deps: ListCasillasDependencies) -> None:
        self._deps = deps

    async def execute(self, *, include_inactive: bool = True) -> list[CasillaDTO]:
        items = await self._deps.casillas.list_all(include_inactive=include_inactive)
        return [
            CasillaDTO(
                id=c.id,
                nombre=c.nombre,
                color=c.color,
                sort_order=c.sort_order,
                is_active=c.is_active,
            )
            for c in items
        ]
