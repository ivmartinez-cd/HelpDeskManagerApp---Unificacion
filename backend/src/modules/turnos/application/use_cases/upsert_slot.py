import uuid
from dataclasses import dataclass

from src.modules.turnos.application.dtos.turno_dtos import (
    CreateSlotCommand,
    SlotDTO,
    UpdateSlotCommand,
)
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import CasillaNotFoundError, SlotNotFoundError
from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository
from src.modules.turnos.domain.services.franja_reglas import validar_franja_titular


@dataclass(frozen=True, slots=True)
class UpsertSlotDependencies:
    slots: SlotRepository
    casillas: CasillaRepository


class UpsertSlot:
    """Caso de uso: crea o actualiza un slot de franja horaria. Mismas
    invariantes que una franja de grilla variante (horario, día 0..6, sin
    solape en la casilla+día) -- ver `franja_reglas`."""

    def __init__(self, deps: UpsertSlotDependencies) -> None:
        self._deps = deps

    async def create(self, command: CreateSlotCommand) -> SlotDTO:
        if await self._deps.casillas.get_by_id(command.casilla_id) is None:
            raise CasillaNotFoundError(command.casilla_id)
        slot = Slot(
            id=uuid.uuid4(),
            casilla_id=command.casilla_id,
            hora_inicio=command.hora_inicio,
            hora_fin=command.hora_fin,
            dia_semana=command.dia_semana,
            sort_order=command.sort_order,
        )
        await self._validar(slot)
        await self._deps.slots.add(slot)
        return _to_dto(slot)

    async def update(self, command: UpdateSlotCommand) -> SlotDTO:
        existing = await self._deps.slots.get_by_id(command.slot_id)
        if existing is None:
            raise SlotNotFoundError(command.slot_id)

        slot = Slot(
            id=command.slot_id,
            casilla_id=existing.casilla_id,
            hora_inicio=command.hora_inicio,
            hora_fin=command.hora_fin,
            dia_semana=command.dia_semana,
            sort_order=existing.sort_order,
        )
        await self._validar(slot)
        await self._deps.slots.save(slot)
        return _to_dto(slot)

    async def _validar(self, slot: Slot) -> None:
        vecinas = await self._deps.slots.list_by_casilla(slot.casilla_id)
        validar_franja_titular(slot, vecinas)


def _to_dto(slot: Slot) -> SlotDTO:
    return SlotDTO(
        id=slot.id,
        casilla_id=slot.casilla_id,
        hora_inicio=slot.hora_inicio,
        hora_fin=slot.hora_fin,
        dia_semana=slot.dia_semana,
        sort_order=slot.sort_order,
        asignaciones=[],
    )
