import uuid
from dataclasses import dataclass

from src.modules.turnos.application.dtos.turno_dtos import ReplaceAssignmentsCommand
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository


@dataclass(frozen=True, slots=True)
class ReplaceSlotAssignmentsDependencies:
    asignaciones: AsignacionRepository


class ReplaceSlotAssignments:
    """Caso de uso: reemplaza la lista de operadores asignados a un slot."""

    def __init__(self, deps: ReplaceSlotAssignmentsDependencies) -> None:
        self._deps = deps

    async def execute(self, command: ReplaceAssignmentsCommand) -> None:
        new_asignaciones = [
            Asignacion(
                id=uuid.uuid4(),
                slot_id=command.slot_id,
                user_id=u_id,
                vigente_desde=command.vigente_desde,
                vigente_hasta=None,
            )
            for u_id in command.user_ids
        ]
        await self._deps.asignaciones.replace_for_slot(
            command.slot_id, command.vigente_desde, new_asignaciones
        )
