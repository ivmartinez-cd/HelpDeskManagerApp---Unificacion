"""Factories del área de clientes."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.import_zone_contacts import (
    ApplyZoneContactsImport,
    GetCustomerZones,
    GetSdsContacts,
    ImportContactsFromSupply,
    PreviewZoneContactsImport,
    ZoneContactImportPorts,
)
from src.modules.insumos.application.use_cases.list_customers import (
    BulkToggleCustomers,
    CustomerListPorts,
    ListCustomers,
    SyncCustomers,
    ToggleCustomer,
)
from src.modules.insumos.application.use_cases.manage_zone_contacts import (
    BulkSeedContacts,
    DeleteZoneContact,
    GetZoneContacts,
    SetZoneContact,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_customer_repository import (
    SqlAlchemyCustomerRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_zone_contact_repository import (
    SqlAlchemyZoneContactRepository,
)
from src.modules.insumos.presentation.wiring import (
    get_insight_gateway,
    get_sds_portal_gateway,
    get_wsayc_gateway,
)


def build_list_customers(session: AsyncSession) -> ListCustomers:
    ports = CustomerListPorts(
        customers=SqlAlchemyCustomerRepository(session),
        zone_contacts=SqlAlchemyZoneContactRepository(session),
    )
    return ListCustomers(ports)


def build_toggle_customer(session: AsyncSession) -> ToggleCustomer:
    return ToggleCustomer(SqlAlchemyCustomerRepository(session))


def build_bulk_toggle_customers(session: AsyncSession) -> BulkToggleCustomers:
    return BulkToggleCustomers(SqlAlchemyCustomerRepository(session))


def build_sync_customers(session: AsyncSession) -> SyncCustomers:
    return SyncCustomers(SqlAlchemyCustomerRepository(session))


def build_get_zone_contacts(session: AsyncSession) -> GetZoneContacts:
    return GetZoneContacts(SqlAlchemyZoneContactRepository(session))


def build_set_zone_contact(session: AsyncSession) -> SetZoneContact:
    return SetZoneContact(SqlAlchemyZoneContactRepository(session))


def build_delete_zone_contact(session: AsyncSession) -> DeleteZoneContact:
    return DeleteZoneContact(SqlAlchemyZoneContactRepository(session))


def build_bulk_seed_contacts(session: AsyncSession) -> BulkSeedContacts:
    return BulkSeedContacts(SqlAlchemyZoneContactRepository(session))


def build_preview_zone_contacts_import(session: AsyncSession) -> PreviewZoneContactsImport:
    ports = ZoneContactImportPorts(
        zone_contacts=SqlAlchemyZoneContactRepository(session),
        insight=get_insight_gateway(),
        portal=get_sds_portal_gateway(),
    )
    return PreviewZoneContactsImport(ports)


def build_apply_zone_contacts_import(session: AsyncSession) -> ApplyZoneContactsImport:
    ports = ZoneContactImportPorts(
        zone_contacts=SqlAlchemyZoneContactRepository(session),
        insight=get_insight_gateway(),
        portal=get_sds_portal_gateway(),
    )
    return ApplyZoneContactsImport(ports)


def build_get_sds_contacts() -> GetSdsContacts:
    return GetSdsContacts(get_insight_gateway())


def build_get_customer_zones() -> GetCustomerZones:
    return GetCustomerZones(get_insight_gateway())


def build_import_contacts_from_supply(session: AsyncSession) -> ImportContactsFromSupply:
    return ImportContactsFromSupply(
        wsayc=get_wsayc_gateway(),
        repo=SqlAlchemyZoneContactRepository(session),
    )
