import uuid
from dataclasses import dataclass

from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository


@dataclass(frozen=True, slots=True)
class DeleteCasillaDependencies:
    casillas: CasillaRepository


class DeleteCasilla:
    """Caso de uso: elimina una casilla."""

    def __init__(self, deps: DeleteCasillaDependencies) -> None:
        self._deps = deps

    async def execute(self, casilla_id: uuid.UUID) -> None:
        await self._deps.casillas.delete(casilla_id)
