from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)


class GetMiOperadorUseCase:
    """Resuelve el operador de Gestión (y su color aproximado) del usuario
    logueado, para pintar el avatar. Superadmin no tiene un operador propio
    (ve todo, sin filtrar)."""

    def __init__(self, repository: CalendarEventRepository) -> None:
        self._repository = repository

    async def execute(self, *, is_superadmin: bool, full_name: str) -> Operador | None:
        if is_superadmin:
            return None
        return await self._repository.find_operador_by_nombre(full_name)
