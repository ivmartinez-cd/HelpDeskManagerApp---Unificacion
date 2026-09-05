import uuid
from dataclasses import dataclass

from src.modules.turnos.domain.errors import SlotEnUsoError, SlotNotFoundError
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
    TurnoAsignacionOverride,
)
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository


@dataclass(frozen=True, slots=True)
class DeleteSlotDependencies:
    slots: SlotRepository
    asignaciones: AsignacionRepository
    overrides: AsignacionOverrideRepository


class DeleteSlot:
    """Caso de uso: elimina un slot y sus asignaciones asociadas. Si una
    cobertura parcial no cancelada lo referencia se rechaza: el CASCADE de
    `turno_asignacion_override_slot` la dejaría con alcance vacío y dejaría
    de cubrir sin aviso. Las grillas de vacaciones no referencian `turno_slot`
    (tienen franjas propias por casilla), así que no bloquean acá."""

    def __init__(self, deps: DeleteSlotDependencies) -> None:
        self._deps = deps

    async def execute(self, slot_id: uuid.UUID) -> None:
        if await self._deps.slots.get_by_id(slot_id) is None:
            raise SlotNotFoundError(slot_id)
        coberturas = [o for o in await self._deps.overrides.list_all() if _referencia(o, slot_id)]
        if coberturas:
            raise SlotEnUsoError(
                f"la referencian {len(coberturas)} cobertura(s) parcial(es) activa(s): "
                + ", ".join(_describir(o) for o in coberturas)
            )
        await self._deps.asignaciones.delete_by_slot(slot_id)
        await self._deps.slots.delete(slot_id)


def _referencia(override: TurnoAsignacionOverride, slot_id: uuid.UUID) -> bool:
    return (
        override.estado != "CANCELADA"
        and override.alcance != "TOTAL"
        and slot_id in override.alcance
    )


def _describir(override: TurnoAsignacionOverride) -> str:
    return f"{override.id} ({override.desde:%d/%m/%Y}-{override.hasta:%d/%m/%Y})"
