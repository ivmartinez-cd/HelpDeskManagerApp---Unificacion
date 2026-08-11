"""Puerto de customer_zone_contacts (contactos por zona de un cliente)."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.zone_contacts import (
    ZoneContactRow,
    ZoneContacts,
)


class ZoneContactRepository(Protocol):
    async def get(self, customer_id: int, zone: str) -> ZoneContacts | None:
        """Contactos de la zona exacta; `zone=""` es la zona default del cliente."""
        ...

    async def list_all(self, customer_id: int) -> list[ZoneContactRow]:
        """Todas las zonas del cliente: named primero (A-Z), zona '' al final."""
        ...

    async def upsert(self, customer_id: int, row: ZoneContactRow) -> None:
        """Upsert de una zona completa."""
        ...

    async def delete(self, customer_id: int, zone: str) -> None:
        ...

    async def bulk_set(
        self, customer_ids: list[int], row: ZoneContactRow
    ) -> int:
        """Upsert de la misma zona (row.zone) para todos los customer_ids. Retorna n afectados."""
        ...

    async def customers_with_contacts(self) -> set[int]:
        """IDs de clientes con al menos un apellido/nombre cargado en alguna zona."""
        ...
