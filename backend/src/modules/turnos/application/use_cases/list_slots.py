import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.turnos.application.dtos.turno_dtos import AsignacionDTO, SlotDTO
from src.modules.turnos.application.fecha_local import hoy_local
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository
from src.modules.turnos.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class ListSlotsDependencies:
    slots: SlotRepository
    asignaciones: AsignacionRepository
    users: UserProvider


class ListSlots:
    """Caso de uso: lista los slots de franjas horarias con sus asignaciones vigentes."""

    def __init__(self, deps: ListSlotsDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, casilla_id: uuid.UUID | None = None, target_date: date | None = None
    ) -> list[SlotDTO]:
        if casilla_id:
            slots = await self._deps.slots.list_by_casilla(casilla_id)
        else:
            slots = await self._deps.slots.list_all()

        effective_date = target_date or hoy_local()
        asignaciones_by_slot = await self._deps.asignaciones.list_by_slots(
            [slot.id for slot in slots], effective_date
        )
        # Nombres resueltos por id, no filtrados por activo: un operador desactivado
        # con una asignación vieja/vigente tiene que seguir mostrando su nombre acá
        # (mismo criterio que GetCurrentShifts), no "Desconocido".
        all_user_ids = {a.user_id for asig_list in asignaciones_by_slot.values() for a in asig_list}
        user_info_map = await self._deps.users.get_users_by_ids(list(all_user_ids))

        return [
            SlotDTO(
                id=slot.id,
                casilla_id=slot.casilla_id,
                hora_inicio=slot.hora_inicio,
                hora_fin=slot.hora_fin,
                dia_semana=slot.dia_semana,
                sort_order=slot.sort_order,
                asignaciones=[
                    AsignacionDTO(
                        id=a.id,
                        slot_id=a.slot_id,
                        user_id=a.user_id,
                        user_name=(
                            user_info_map[a.user_id].full_name
                            if a.user_id in user_info_map
                            else None
                        ),
                        vigente_desde=a.vigente_desde,
                        vigente_hasta=a.vigente_hasta,
                    )
                    for a in asignaciones_by_slot.get(slot.id, [])
                ],
            )
            for slot in slots
        ]
