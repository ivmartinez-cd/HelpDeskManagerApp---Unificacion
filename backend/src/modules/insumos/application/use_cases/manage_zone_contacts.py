"""Casos de uso de CRUD de contactos por zona y operaciones de siembra."""

from src.modules.insumos.domain.repositories.zone_contact_repository import ZoneContactRepository
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContactRow


class GetZoneContacts:
    def __init__(self, repo: ZoneContactRepository) -> None:
        self._repo = repo

    async def execute(self, customer_id: int) -> list[ZoneContactRow]:
        return await self._repo.list_all(customer_id)


class SetZoneContact:
    def __init__(self, repo: ZoneContactRepository) -> None:
        self._repo = repo

    async def execute(self, customer_id: int, row: ZoneContactRow) -> None:
        await self._repo.upsert(customer_id, row)


class DeleteZoneContact:
    def __init__(self, repo: ZoneContactRepository) -> None:
        self._repo = repo

    async def execute(self, customer_id: int, zone: str) -> None:
        await self._repo.delete(customer_id, zone)


class BulkSeedContacts:
    def __init__(self, repo: ZoneContactRepository) -> None:
        self._repo = repo

    async def execute(self, customer_ids: list[int], row: ZoneContactRow) -> int:
        return await self._repo.bulk_set(customer_ids, row)
