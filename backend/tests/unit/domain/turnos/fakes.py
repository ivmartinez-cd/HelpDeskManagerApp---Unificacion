"""Fakes en memoria de los puertos de turnos para tests unitarios."""

import uuid
from datetime import date, timedelta

from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.user_provider import UserInfo


class FakeCasillaRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Casilla] = {}

    async def get_by_id(self, casilla_id: uuid.UUID) -> Casilla | None:
        return self.rows.get(casilla_id)

    async def list_all(self, *, include_inactive: bool = False) -> list[Casilla]:
        items = self.rows.values()
        if not include_inactive:
            items = [c for c in items if c.is_active]
        return sorted(items, key=lambda c: (c.sort_order, c.nombre))

    async def add(self, casilla: Casilla) -> None:
        self.rows[casilla.id] = casilla

    async def save(self, casilla: Casilla) -> None:
        self.rows[casilla.id] = casilla

    async def delete(self, casilla_id: uuid.UUID) -> None:
        self.rows.pop(casilla_id, None)


class FakeSlotRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Slot] = {}

    async def get_by_id(self, slot_id: uuid.UUID) -> Slot | None:
        return self.rows.get(slot_id)

    async def list_by_casilla(self, casilla_id: uuid.UUID) -> list[Slot]:
        return [s for s in self.rows.values() if s.casilla_id == casilla_id]

    async def list_all(self) -> list[Slot]:
        return list(self.rows.values())

    async def add(self, slot: Slot) -> None:
        self.rows[slot.id] = slot

    async def save(self, slot: Slot) -> None:
        self.rows[slot.id] = slot

    async def delete(self, slot_id: uuid.UUID) -> None:
        self.rows.pop(slot_id, None)


class FakeAsignacionRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Asignacion] = {}
        self.list_by_slot_calls = 0
        self.list_by_slots_calls = 0

    async def list_by_slot(self, slot_id: uuid.UUID) -> list[Asignacion]:
        self.list_by_slot_calls += 1
        return [a for a in self.rows.values() if a.slot_id == slot_id]

    async def list_by_slots(
        self, slot_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[Asignacion]]:
        self.list_by_slots_calls += 1
        grouped: dict[uuid.UUID, list[Asignacion]] = {}
        for a in self.rows.values():
            if a.slot_id in slot_ids:
                grouped.setdefault(a.slot_id, []).append(a)
        return grouped

    async def list_active_on_date(self, target_date: date) -> list[Asignacion]:
        return [
            a
            for a in self.rows.values()
            if a.vigente_desde <= target_date
            and (a.vigente_hasta is None or a.vigente_hasta >= target_date)
        ]

    async def replace_for_slot(
        self, slot_id: uuid.UUID, effective_date: date, asignaciones: list[Asignacion]
    ) -> None:
        for a in list(self.rows.values()):
            if a.slot_id != slot_id or a.vigente_hasta is not None:
                continue
            close_at = effective_date - timedelta(days=1)
            if a.vigente_desde > close_at:
                del self.rows[a.id]
            else:
                a.vigente_hasta = close_at
        for a in asignaciones:
            self.rows[a.id] = a

    async def delete_by_slot(self, slot_id: uuid.UUID) -> None:
        for a_id in [a.id for a in self.rows.values() if a.slot_id == slot_id]:
            del self.rows[a_id]


class FakeUserProvider:
    def __init__(self) -> None:
        self.users: dict[uuid.UUID, UserInfo] = {}
        self.active_ids: set[uuid.UUID] = set()

    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]:
        return {uid: self.users[uid] for uid in user_ids if uid in self.users}

    async def list_all_active_users(self) -> list[UserInfo]:
        return [u for uid, u in self.users.items() if uid in self.active_ids]
