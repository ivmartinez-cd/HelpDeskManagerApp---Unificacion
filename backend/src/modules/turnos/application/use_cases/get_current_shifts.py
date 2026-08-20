from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    CurrentShiftsDTO,
    VarianteActivaDTO,
)
from src.modules.turnos.application.dtos.turno_dtos import OperatorShiftView, ResolvedShiftDTO
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository
from src.modules.turnos.domain.repositories.grilla_variante_repository import (
    GrillaVarianteRepository,
)
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository
from src.modules.turnos.domain.repositories.user_provider import UserProvider
from src.modules.turnos.domain.services.turno_resolver import ResolvedSlotShift, TurnoResolver

_ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


@dataclass(frozen=True, slots=True)
class GetCurrentShiftsDependencies:
    casillas: CasillaRepository
    slots: SlotRepository
    asignaciones: AsignacionRepository
    users: UserProvider
    overrides: AsignacionOverrideRepository
    variantes: GrillaVarianteRepository


class GetCurrentShifts:
    """Caso de uso: obtiene el estado actual y próximo de turnos en las
    casillas. Si hay una grilla de vacaciones vigente hoy (ADR-025), las
    franjas salen de ella y el resultado trae su cabecera en
    `variante_activa`; si no, de la grilla titular."""

    def __init__(self, deps: GetCurrentShiftsDependencies) -> None:
        self._deps = deps
        self._resolver = TurnoResolver()

    async def execute(self, *, now_datetime: datetime | None = None) -> CurrentShiftsDTO:
        now = now_datetime or datetime.now(_ARGENTINA_TZ)
        target_date = now.date()

        casillas = await self._deps.casillas.list_all(include_inactive=False)
        slots = await self._deps.slots.list_all()
        asignaciones = await self._deps.asignaciones.list_active_on_date(target_date)
        variante = await self._deps.variantes.find_vigente(target_date)

        if variante is not None:
            ausente_ids = list({u for s in variante.slots for u in s.user_ids})
        else:
            ausente_ids = list({a.user_id for a in asignaciones})
        overrides_por_ausente = await self._deps.overrides.list_activos_por_ausentes(ausente_ids)

        resolved = self._resolver.resolve_shifts(
            casillas=casillas,
            slots=slots,
            asignaciones=asignaciones,
            target_date=target_date,
            target_time=now.time(),
            overrides_por_ausente=overrides_por_ausente,
            variante=variante,
        )
        return CurrentShiftsDTO(
            shifts=await self._to_dtos(resolved),
            variante_activa=_variante_activa(variante),
        )

    async def _to_dtos(self, resolved: list[ResolvedSlotShift]) -> list[ResolvedShiftDTO]:
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


def _variante_activa(variante: GrillaVariante | None) -> VarianteActivaDTO | None:
    if variante is None:
        return None
    return VarianteActivaDTO(
        id=variante.id, motivo=variante.motivo, desde=variante.desde, hasta=variante.hasta
    )
