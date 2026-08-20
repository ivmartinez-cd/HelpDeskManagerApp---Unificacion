from dataclasses import dataclass

from src.modules.turnos.application.dtos.turno_dtos import AsignacionOverrideDTO
from src.modules.turnos.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.turnos.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class ListAsignacionOverridesDependencies:
    overrides: AsignacionOverrideRepository
    users: UserProvider


class ListAsignacionOverrides:
    """Caso de uso: lista todas las coberturas (activas y canceladas), más
    recientes primero por fecha de inicio."""

    def __init__(self, deps: ListAsignacionOverridesDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[AsignacionOverrideDTO]:
        overrides = await self._deps.overrides.list_all()
        operador_ids = {
            operador_id
            for o in overrides
            for operador_id in (o.operador_ausente_id, o.operador_reemplazante_id)
        }
        users = await self._deps.users.get_users_by_ids(list(operador_ids))
        return [
            build_asignacion_override_dto(o, users)
            for o in sorted(overrides, key=lambda o: o.desde, reverse=True)
        ]
