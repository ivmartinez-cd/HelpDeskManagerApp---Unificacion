"""Casos de uso de la pantalla Clientes: listado, toggle, sincronización."""

from dataclasses import dataclass

from src.modules.insumos.domain.repositories.customer_repository import CustomerRepository
from src.modules.insumos.domain.repositories.zone_contact_repository import ZoneContactRepository
from src.modules.insumos.domain.value_objects.zone_contacts import Customer


@dataclass
class CustomerListPorts:
    customers: CustomerRepository
    zone_contacts: ZoneContactRepository


class ListCustomers:
    def __init__(self, ports: CustomerListPorts) -> None:
        self._ports = ports

    async def execute(self) -> list[Customer]:
        customers = await self._ports.customers.list_all()
        with_contacts = await self._ports.zone_contacts.customers_with_contacts()
        return [
            Customer(
                customer_id=c.customer_id,
                name=c.name,
                enabled=c.enabled,
                has_contacts=c.customer_id in with_contacts,
            )
            for c in customers
        ]


class ToggleCustomer:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, customer_id: int, enabled: bool) -> None:
        await self._repo.set_enabled(customer_id, enabled)


class BulkToggleCustomers:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, enabled: bool) -> None:
        await self._repo.bulk_toggle(enabled)


class SyncCustomers:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, customers: list[dict[str, object]]) -> int:
        await self._repo.sync(customers)
        return len(customers)
