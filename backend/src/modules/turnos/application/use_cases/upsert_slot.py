import uuid
from dataclasses import dataclass

from src.modules.turnos.application.dtos.turno_dtos import (
    CreateSlotCommand,
    SlotDTO,
    UpdateSlotCommand,
)
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository


@dataclass(frozen=True, slots=True)
class UpsertSlotDependencies:
    slots: SlotRepository


class UpsertSlot:
    """Caso de uso: crea o actualiza un slot de franja horaria."""

    def __init__(self, deps: UpsertSlotDependencies) -> None:
        self._deps = deps

    async def create(self, command: CreateSlotCommand) -> SlotDTO:
        slot = Slot(
            id=uuid.uuid4(),
            casilla_id=command.casilla_id,
            hora_inicio=command.hora_inicio,
            hora_fin=command.hora_fin,
            dia_semana=command.dia_semana,
            sort_order=command.sort_order,
        )
        await self._deps.slots.add(slot)
        return SlotDTO(
            id=slot.id,
            casilla_id=slot.casilla_id,
            hora_inicio=slot.hora_inicio,
            hora_fin=slot.hora_fin,
            dia_semana=slot.dia_semana,
            sort_order=slot.sort_order,
            asignaciones=[],
        )

    async def update(self, command: UpdateSlotCommand) -> SlotDTO:
        existing = await self._deps.slots.get_by_id(command.slot_id)
        if existing is None:
            raise ValueError(f"Slot {command.slot_id} no existe")

        slot = Slot(
            id=command.slot_id,
            casilla_id=existing.casilla_id,
            hora_inicio=command.hora_inicio,
            hora_fin=command.hora_fin,
            dia_semana=command.dia_semana,
            sort_order=existing.sort_order,
        )
        await self._deps.slots.save(slot)
        return SlotDTO(
            id=slot.id,
            casilla_id=slot.casilla_id,
            hora_inicio=slot.hora_inicio,
            hora_fin=slot.hora_fin,
            dia_semana=slot.dia_semana,
            sort_order=slot.sort_order,
            asignaciones=[],
        )
