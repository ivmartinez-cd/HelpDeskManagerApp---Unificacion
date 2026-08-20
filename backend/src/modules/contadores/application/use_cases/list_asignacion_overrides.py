from dataclasses import dataclass

from src.modules.contadores.application.dtos.asignacion_override_dto import AsignacionOverrideDTO
from src.modules.contadores.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.contadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)


@dataclass(frozen=True, slots=True)
class ListAsignacionOverridesDependencies:
    overrides: AsignacionOverrideRepository
    calendar: CalendarEventRepository


class ListAsignacionOverrides:
    """Caso de uso: lista todos los overrides (activos y cancelados), más
    recientes primero por fecha de inicio."""

    def __init__(self, deps: ListAsignacionOverridesDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[AsignacionOverrideDTO]:
        overrides = await self._deps.overrides.list_all()
        operadores = await self._deps.calendar.list_operadores()
        por_id = {op.id: op for op in operadores}
        return [
            build_asignacion_override_dto(o, por_id)
            for o in sorted(overrides, key=lambda o: o.desde, reverse=True)
        ]
