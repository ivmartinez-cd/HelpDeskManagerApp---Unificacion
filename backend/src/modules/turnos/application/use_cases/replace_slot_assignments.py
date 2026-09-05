import uuid
from dataclasses import dataclass

from src.modules.turnos.application.dtos.turno_dtos import ReplaceAssignmentsCommand
from src.modules.turnos.application.use_cases.usuarios_support import validar_usuarios_existen
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.errors import SlotNotFoundError
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository
from src.modules.turnos.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class ReplaceSlotAssignmentsDependencies:
    asignaciones: AsignacionRepository
    slots: SlotRepository
    users: UserProvider


class ReplaceSlotAssignments:
    """Caso de uso: reemplaza la lista de operadores asignados a un slot."""

    def __init__(self, deps: ReplaceSlotAssignmentsDependencies) -> None:
        self._deps = deps

    async def execute(self, command: ReplaceAssignmentsCommand) -> None:
        if await self._deps.slots.get_by_id(command.slot_id) is None:
            raise SlotNotFoundError(command.slot_id)
        unique_user_ids = list(dict.fromkeys(command.user_ids))
        await validar_usuarios_existen(self._deps.users, unique_user_ids)
        new_asignaciones = [
            Asignacion(
                id=uuid.uuid4(),
                slot_id=command.slot_id,
                user_id=u_id,
                vigente_desde=command.vigente_desde,
                vigente_hasta=None,
            )
            for u_id in unique_user_ids
        ]
        await self._deps.asignaciones.replace_for_slot(
            command.slot_id, command.vigente_desde, new_asignaciones
        )
