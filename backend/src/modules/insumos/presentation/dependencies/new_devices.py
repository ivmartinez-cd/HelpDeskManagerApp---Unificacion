"""Factories de la pantalla de equipos sin registrar y su sincronización."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.list_new_devices import (
    CountNewDevices,
    DismissNewDevice,
    ListNewDevices,
    NewDevicesPorts,
)
from src.modules.insumos.application.use_cases.sync_new_devices import (
    SyncNewDevices,
    SyncNewDevicesPorts,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_customer_config_repository import (  # noqa: E501
    SqlAlchemyCustomerConfigRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_known_device_repository import (  # noqa: E501
    SqlAlchemyKnownDeviceRepository,
)
from src.modules.insumos.presentation.wiring import get_insight_gateway
from src.shared.infrastructure.config.settings import get_settings


def _ports(session: AsyncSession) -> NewDevicesPorts:
    return NewDevicesPorts(devices=SqlAlchemyKnownDeviceRepository(session))


def build_list_new_devices(session: AsyncSession) -> ListNewDevices:
    return ListNewDevices(_ports(session), get_settings().insight_base_url)


def build_count_new_devices(session: AsyncSession) -> CountNewDevices:
    return CountNewDevices(_ports(session))


def build_dismiss_new_device(session: AsyncSession) -> DismissNewDevice:
    return DismissNewDevice(_ports(session))


def build_sync_new_devices(session: AsyncSession) -> SyncNewDevices:
    ports = SyncNewDevicesPorts(
        insight=get_insight_gateway(),
        customers=SqlAlchemyCustomerConfigRepository(session),
        devices=SqlAlchemyKnownDeviceRepository(session),
    )
    return SyncNewDevices(ports)
