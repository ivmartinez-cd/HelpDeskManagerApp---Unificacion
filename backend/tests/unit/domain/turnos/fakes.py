"""Fakes en memoria de los puertos de turnos para tests unitarios."""

import uuid
from datetime import date, timedelta

from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    TurnoAsignacionOverride,
)
from src.modules.turnos.domain.repositories.ausencias_lookup import AusenciaAprobada
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
        self.list_by_slots_calls = 0

    async def list_by_slots(
        self, slot_ids: list[uuid.UUID], target_date: date
    ) -> dict[uuid.UUID, list[Asignacion]]:
        self.list_by_slots_calls += 1
        grouped: dict[uuid.UUID, list[Asignacion]] = {}
        for a in self.rows.values():
            if (
                a.slot_id in slot_ids
                and a.vigente_desde <= target_date
                and (a.vigente_hasta is None or a.vigente_hasta >= target_date)
            ):
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


class FakeAsignacionOverrideRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, TurnoAsignacionOverride] = {}

    async def create(self, override: TurnoAsignacionOverride) -> None:
        self.rows[override.id] = override

    async def list_all(self) -> list[TurnoAsignacionOverride]:
        return list(self.rows.values())

    async def get_by_id(self, override_id: uuid.UUID) -> TurnoAsignacionOverride | None:
        return self.rows.get(override_id)

    async def list_activos_por_ausente(
        self, operador_ausente_id: uuid.UUID
    ) -> list[TurnoAsignacionOverride]:
        return [
            o
            for o in self.rows.values()
            if o.operador_ausente_id == operador_ausente_id and o.estado == "ACTIVA"
        ]

    async def list_activos_por_ausentes(
        self, operador_ausente_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[TurnoAsignacionOverride]]:
        grouped: dict[uuid.UUID, list[TurnoAsignacionOverride]] = {}
        for o in self.rows.values():
            if o.operador_ausente_id in operador_ausente_ids and o.estado == "ACTIVA":
                grouped.setdefault(o.operador_ausente_id, []).append(o)
        return grouped

    async def update(self, override: TurnoAsignacionOverride) -> None:
        if override.id in self.rows:
            self.rows[override.id] = override

    async def cancelar(self, override_id: uuid.UUID) -> None:
        if override_id in self.rows:
            self.rows[override_id].estado = "CANCELADA"


class FakeGrillaVarianteRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, GrillaVariante] = {}

    async def create(self, variante: GrillaVariante) -> None:
        self.rows[variante.id] = variante

    async def update(self, variante: GrillaVariante) -> None:
        if variante.id in self.rows:
            self.rows[variante.id] = variante

    async def get_by_id(self, variante_id: uuid.UUID) -> GrillaVariante | None:
        return self.rows.get(variante_id)

    async def list_all(self) -> list[GrillaVariante]:
        return list(self.rows.values())

    async def list_activas(self) -> list[GrillaVariante]:
        return [v for v in self.rows.values() if v.estado == "ACTIVA"]

    async def find_vigente(self, fecha: date) -> GrillaVariante | None:
        return next((v for v in self.rows.values() if v.vigente_en(fecha)), None)

    async def cancelar(self, variante_id: uuid.UUID) -> None:
        if variante_id in self.rows:
            self.rows[variante_id].estado = "CANCELADA"


class FakeAusenciasLookup:
    def __init__(self) -> None:
        self.rows: list[AusenciaAprobada] = []

    async def ausencias_aprobadas_en(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        return [
            a
            for a in self.rows
            if a.user_id in user_ids and not (a.desde > hasta or desde > a.hasta)
        ]


class FakeUserProvider:
    def __init__(self) -> None:
        self.users: dict[uuid.UUID, UserInfo] = {}
        self.active_ids: set[uuid.UUID] = set()

    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]:
        return {uid: self.users[uid] for uid in user_ids if uid in self.users}

    async def list_all_active_users(self) -> list[UserInfo]:
        return [u for uid, u in self.users.items() if uid in self.active_ids]
