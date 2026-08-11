"""Factories de la pantalla de equipos offline."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases._offline_snapshot import OfflineSnapshotPorts
from src.modules.insumos.application.use_cases.delete_offline_devices import (
    DeleteOfflineDevices,
    DeleteOfflineDevicesPorts,
)
from src.modules.insumos.application.use_cases.list_offline_devices import (
    CountOfflineCandidates,
    DismissOfflineDevice,
    ListOfflineDevices,
    ListOfflineOutages,
)
from src.modules.insumos.application.use_cases.sync_monitor_status import (
    SyncMonitorStatus,
    SyncMonitorStatusPorts,
)
from src.modules.insumos.application.use_cases.verify_offline_devices import (
    VerifyOfflineDevices,
    VerifyOfflineDevicesPorts,
)
from src.modules.insumos.domain.value_objects.insumos_settings import (
    InsumosSettings,
    settings_from_raw,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_dca_monitor_repository import (
    SqlAlchemyDcaMonitorRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_known_device_repository import (
    SqlAlchemyKnownDeviceRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_order_audit_repository import (
    SqlAlchemyOrderAuditRepository,
)
from src.modules.insumos.presentation.wiring import (
    app_timezone,
    get_insight_gateway,
    get_offline_delete_lock,
    get_offline_verify_lock,
    get_sds_portal_gateway,
    get_wsayc_gateway,
)
from src.shared.infrastructure.config.settings import get_settings


async def _load_snapshot_ports(
    session: AsyncSession,
) -> tuple[OfflineSnapshotPorts, InsumosSettings]:
    raw_settings = await SqlAlchemyInsumosSettingsRepository(session).get_all()
    settings = settings_from_raw(raw_settings)
    ports = OfflineSnapshotPorts(
        devices=SqlAlchemyKnownDeviceRepository(session),
        monitors=SqlAlchemyDcaMonitorRepository(session),
    )
    return ports, settings


async def build_list_offline_devices(session: AsyncSession) -> ListOfflineDevices:
    ports, settings = await _load_snapshot_ports(session)
    return ListOfflineDevices(ports, settings)


async def build_list_offline_outages(session: AsyncSession) -> ListOfflineOutages:
    ports, settings = await _load_snapshot_ports(session)
    return ListOfflineOutages(ports, settings)


async def build_count_offline_candidates(session: AsyncSession) -> CountOfflineCandidates:
    ports, settings = await _load_snapshot_ports(session)
    return CountOfflineCandidates(ports, settings)


def build_dismiss_offline_device(session: AsyncSession) -> DismissOfflineDevice:
    ports = OfflineSnapshotPorts(
        devices=SqlAlchemyKnownDeviceRepository(session),
        monitors=SqlAlchemyDcaMonitorRepository(session),
    )
    return DismissOfflineDevice(ports)


def build_sync_monitor_status(session: AsyncSession) -> SyncMonitorStatus:
    ports = SyncMonitorStatusPorts(
        insight=get_insight_gateway(),
        monitors=SqlAlchemyDcaMonitorRepository(session),
    )
    return SyncMonitorStatus(ports)


async def build_verify_offline_devices(session: AsyncSession) -> VerifyOfflineDevices:
    ports, settings = await _load_snapshot_ports(session)
    verify_ports = VerifyOfflineDevicesPorts(
        snapshot=ports,
        devices=SqlAlchemyKnownDeviceRepository(session),
        wsayc=get_wsayc_gateway(),
        verify_lock=get_offline_verify_lock(),
        sync_monitor_ports=SyncMonitorStatusPorts(
            insight=get_insight_gateway(),
            monitors=SqlAlchemyDcaMonitorRepository(session),
        ),
    )
    return VerifyOfflineDevices(verify_ports, settings)


async def build_delete_offline_devices(session: AsyncSession) -> DeleteOfflineDevices:
    raw_settings = await SqlAlchemyInsumosSettingsRepository(session).get_all()
    settings = settings_from_raw(raw_settings)
    snapshot_ports = OfflineSnapshotPorts(
        devices=SqlAlchemyKnownDeviceRepository(session),
        monitors=SqlAlchemyDcaMonitorRepository(session),
    )
    delete_ports = DeleteOfflineDevicesPorts(
        snapshot=snapshot_ports,
        devices=SqlAlchemyKnownDeviceRepository(session),
        audit=SqlAlchemyOrderAuditRepository(session),
        portal=get_sds_portal_gateway(),
        delete_lock=get_offline_delete_lock(),
    )
    return DeleteOfflineDevices(
        delete_ports,
        settings,
        dry_run=get_settings().sds_delete_dry_run,
        tz=app_timezone(),
    )
