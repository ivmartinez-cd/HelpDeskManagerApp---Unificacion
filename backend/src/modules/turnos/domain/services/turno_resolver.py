import uuid
from dataclasses import dataclass
from datetime import date, time

from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    TurnoAsignacionOverride,
)
from src.shared.domain.services.asignacion_override_resolver import resolver_operador_efectivo


@dataclass(frozen=True, slots=True)
class ResolvedSlotShift:
    slot_id: uuid.UUID
    casilla_id: uuid.UUID
    casilla_nombre: str
    casilla_color: str | None
    hora_inicio: time
    hora_fin: time
    dia_semana: int
    user_ids: list[uuid.UUID]
    is_current: bool
    is_next: bool


class TurnoResolver:
    """Calcula el estado actual y próximo de turnos para una fecha y hora."""

    def resolve_shifts(
        self,
        *,
        casillas: list[Casilla],
        slots: list[Slot],
        asignaciones: list[Asignacion],
        target_date: date,
        target_time: time,
        overrides_por_ausente: dict[uuid.UUID, list[TurnoAsignacionOverride]] | None = None,
    ) -> list[ResolvedSlotShift]:
        dia_semana = target_date.weekday()
        casillas_dict = {c.id: c for c in casillas if c.is_active}
        active_slots = [
            s for s in slots if s.casilla_id in casillas_dict and s.dia_semana == dia_semana
        ]
        active_slots.sort(key=lambda s: (casillas_dict[s.casilla_id].sort_order, s.hora_inicio))

        slot_users = self._map_slot_users(
            asignaciones, target_date, overrides_por_ausente or {}
        )
        return [
            self._build_resolved_shift(
                slot=slot,
                casilla=casillas_dict[slot.casilla_id],
                user_ids=slot_users.get(slot.id, []),
                target_time=target_time,
                all_day_slots=[s for s in active_slots if s.casilla_id == slot.casilla_id],
            )
            for slot in active_slots
        ]

    def _map_slot_users(
        self,
        asignaciones: list[Asignacion],
        target_date: date,
        overrides_por_ausente: dict[uuid.UUID, list[TurnoAsignacionOverride]],
    ) -> dict[uuid.UUID, list[uuid.UUID]]:
        mapping: dict[uuid.UUID, list[uuid.UUID]] = {}
        for a in asignaciones:
            is_active_start = a.vigente_desde <= target_date
            is_active_end = a.vigente_hasta is None or a.vigente_hasta >= target_date
            if is_active_start and is_active_end:
                mapping.setdefault(a.slot_id, []).append(a.user_id)
        if not overrides_por_ausente:
            return mapping
        return {
            slot_id: list(
                dict.fromkeys(
                    self._operador_efectivo(
                        user_id, slot_id, target_date, overrides_por_ausente
                    )
                    for user_id in user_ids
                )
            )
            for slot_id, user_ids in mapping.items()
        }

    def _operador_efectivo(
        self,
        user_id: uuid.UUID,
        slot_id: uuid.UUID,
        target_date: date,
        overrides_por_ausente: dict[uuid.UUID, list[TurnoAsignacionOverride]],
    ) -> uuid.UUID:
        efectivo = resolver_operador_efectivo(
            user_id, slot_id, target_date, overrides_por_ausente.get(user_id, [])
        )
        assert efectivo is not None  # `user_id` (operador_original) nunca es None acá
        return efectivo

    def _build_resolved_shift(
        self,
        *,
        slot: Slot,
        casilla: Casilla,
        user_ids: list[uuid.UUID],
        target_time: time,
        all_day_slots: list[Slot],
    ) -> ResolvedSlotShift:
        is_current = slot.hora_inicio <= target_time < slot.hora_fin
        is_next = self._check_is_next(slot, target_time, all_day_slots)
        return ResolvedSlotShift(
            slot_id=slot.id,
            casilla_id=casilla.id,
            casilla_nombre=casilla.nombre,
            casilla_color=casilla.color,
            hora_inicio=slot.hora_inicio,
            hora_fin=slot.hora_fin,
            dia_semana=slot.dia_semana,
            user_ids=user_ids,
            is_current=is_current,
            is_next=is_next,
        )

    def _check_is_next(self, slot: Slot, target_time: time, all_day_slots: list[Slot]) -> bool:
        upcoming_slots = [s for s in all_day_slots if s.hora_inicio > target_time]
        if not upcoming_slots:
            return False
        next_slot = min(upcoming_slots, key=lambda s: s.hora_inicio)
        return slot.id == next_slot.id
