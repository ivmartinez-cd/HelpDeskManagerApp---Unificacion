"""Fakes en memoria de los puertos de prestadores para tests unitarios."""

import uuid
from datetime import date, timedelta

from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.siges_prestador_gateway import (
    SigesPrestadorInfo,
)
from src.modules.prestadores.domain.repositories.user_provider import UserInfo


class FakePrestadorRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Prestador] = {}

    async def get_by_id(self, prestador_id: uuid.UUID) -> Prestador | None:
        return self.rows.get(prestador_id)

    async def get_by_siges_empresa_id(self, siges_empresa_id: int) -> Prestador | None:
        for p in self.rows.values():
            if p.siges_empresa_id == siges_empresa_id:
                return p
        return None

    async def list_all(self, *, include_inactive: bool = False) -> list[Prestador]:
        items = self.rows.values()
        if not include_inactive:
            items = [p for p in items if p.is_active]
        return sorted(items, key=lambda p: p.den_comercial)

    async def add(self, prestador: Prestador) -> None:
        self.rows[prestador.id] = prestador

    async def save(self, prestador: Prestador) -> None:
        self.rows[prestador.id] = prestador


class FakeContactoRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, ContactoPrestador] = {}

    async def get_by_id(self, contacto_id: uuid.UUID) -> ContactoPrestador | None:
        return self.rows.get(contacto_id)

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[ContactoPrestador]:
        return sorted(
            (c for c in self.rows.values() if c.prestador_id == prestador_id),
            key=lambda c: c.sort_order,
        )

    async def list_by_prestadores(
        self, prestador_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[ContactoPrestador]]:
        grouped: dict[uuid.UUID, list[ContactoPrestador]] = {}
        for c in self.rows.values():
            if c.prestador_id in prestador_ids:
                grouped.setdefault(c.prestador_id, []).append(c)
        return grouped

    async def add(self, contacto: ContactoPrestador) -> None:
        self.rows[contacto.id] = contacto

    async def save(self, contacto: ContactoPrestador) -> None:
        self.rows[contacto.id] = contacto

    async def delete(self, contacto_id: uuid.UUID) -> None:
        self.rows.pop(contacto_id, None)


class FakeAsignacionHistorialRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, AsignacionHistorial] = {}

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[AsignacionHistorial]:
        return [t for t in self.rows.values() if t.prestador_id == prestador_id]

    async def reasignar(
        self, prestador_id: uuid.UUID, operador_id: uuid.UUID | None, desde: date
    ) -> None:
        close_at = desde - timedelta(days=1)
        for tramo in list(self.rows.values()):
            if tramo.prestador_id != prestador_id or tramo.hasta is not None:
                continue
            if tramo.desde > close_at:
                del self.rows[tramo.id]
            else:
                tramo.hasta = close_at
        nuevo = AsignacionHistorial(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            operador_id=operador_id,
            desde=desde,
            hasta=None,
        )
        self.rows[nuevo.id] = nuevo


class FakeUserProvider:
    def __init__(self) -> None:
        self.users: dict[uuid.UUID, UserInfo] = {}
        self.active_ids: set[uuid.UUID] = set()

    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]:
        return {uid: self.users[uid] for uid in user_ids if uid in self.users}

    async def list_all_active_users(self) -> list[UserInfo]:
        return [u for uid, u in self.users.items() if uid in self.active_ids]


class FakeSigesPrestadorGateway:
    def __init__(self) -> None:
        self.por_id: dict[int, SigesPrestadorInfo] = {}
        self.calls: list[list[int]] = []

    async def find_by_siges_ids(self, siges_empresa_ids: list[int]) -> list[SigesPrestadorInfo]:
        self.calls.append(siges_empresa_ids)
        return [self.por_id[i] for i in siges_empresa_ids if i in self.por_id]
