import uuid
from dataclasses import dataclass

from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository


@dataclass(frozen=True, slots=True)
class DeleteSlotDependencies:
    slots: SlotRepository
    asignaciones: AsignacionRepository


class DeleteSlot:
    """Caso de uso: elimina un slot y sus asignaciones asociadas."""

    def __init__(self, deps: DeleteSlotDependencies) -> None:
        self._deps = deps

    async def execute(self, slot_id: uuid.UUID) -> None:
        await self._deps.asignaciones.delete_by_slot(slot_id)
        await self._deps.slots.delete(slot_id)
