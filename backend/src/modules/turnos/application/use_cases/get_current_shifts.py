from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from src.modules.turnos.application.dtos.turno_dtos import OperatorShiftView, ResolvedShiftDTO
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository
from src.modules.turnos.domain.repositories.user_provider import UserProvider
from src.modules.turnos.domain.services.turno_resolver import TurnoResolver

_ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


@dataclass(frozen=True, slots=True)
class GetCurrentShiftsDependencies:
    casillas: CasillaRepository
    slots: SlotRepository
    asignaciones: AsignacionRepository
    users: UserProvider


class GetCurrentShifts:
    """Caso de uso: obtiene el estado actual y próximo de turnos en las casillas."""

    def __init__(self, deps: GetCurrentShiftsDependencies) -> None:
        self._deps = deps
        self._resolver = TurnoResolver()

    async def execute(
        self, *, now_datetime: datetime | None = None
    ) -> list[ResolvedShiftDTO]:
        now = now_datetime or datetime.now(_ARGENTINA_TZ)
        target_date = now.date()
        target_time = now.time()

        casillas = await self._deps.casillas.list_all(include_inactive=False)
        slots = await self._deps.slots.list_all()
        asignaciones = await self._deps.asignaciones.list_active_on_date(target_date)

        resolved = self._resolver.resolve_shifts(
            casillas=casillas,
            slots=slots,
            asignaciones=asignaciones,
            target_date=target_date,
            target_time=target_time,
        )

        all_user_ids = {u_id for shift in resolved for u_id in shift.user_ids}
        user_info_map = await self._deps.users.get_users_by_ids(list(all_user_ids))

        return [
            ResolvedShiftDTO(
                slot_id=shift.slot_id,
                casilla_id=shift.casilla_id,
                casilla_nombre=shift.casilla_nombre,
                casilla_color=shift.casilla_color,
                hora_inicio=shift.hora_inicio,
                hora_fin=shift.hora_fin,
                dia_semana=shift.dia_semana,
                is_current=shift.is_current,
                is_next=shift.is_next,
                operadores=[
                    OperatorShiftView(
                        user_id=u_id,
                        user_name=user_info_map[u_id].full_name
                        if u_id in user_info_map
                        else "Desconocido",
                        color=user_info_map[u_id].color if u_id in user_info_map else None,
                    )
                    for u_id in shift.user_ids
                ],
            )
            for shift in resolved
        ]
