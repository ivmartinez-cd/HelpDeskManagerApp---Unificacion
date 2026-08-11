"""Puerto de customer_zone_contacts (contactos por zona de un cliente)."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContacts


class ZoneContactRepository(Protocol):
    async def get(self, customer_id: int, zone: str) -> ZoneContacts | None:
        """Contactos de la zona exacta; `zone=""` es la zona default del cliente."""
        ...
