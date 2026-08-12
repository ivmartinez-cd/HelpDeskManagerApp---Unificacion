"""Implementación Postgres del puerto KnownDeviceRepository (tabla known_devices)."""

from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from itertools import batched

from sqlalchemy import ColumnElement, case, delete, func, select, update
from sqlalchemy.dialects.postgresql import Insert, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.known_device import (
    MONITORED_STATUSES,
    DeviceInventoryEntry,
    KnownDevice,
)
from src.modules.insumos.domain.value_objects.offline_device import (
    DeviceLocationUpdate,
    OfflineDevice,
)
from src.modules.insumos.infrastructure.models.customer_config_model import (
    CustomerConfigModel,
)
from src.modules.insumos.infrastructure.models.known_device_model import KnownDeviceModel

MONITORED = "Y"

# asyncpg tiene un límite duro de 32767 parámetros bind por query. El inventario real
# completo (5169 equipos × 10 columnas en el upsert) lo supera, así que toda operación
# sobre el set completo va en lotes: 1000 filas × 10 columnas = 10000 parámetros.
BATCH_ROWS = 1000


class SqlAlchemyKnownDeviceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_monitored_by_customer(self) -> dict[int, int]:
        stmt = (
            select(KnownDeviceModel.customer_id, func.count())
            .where(KnownDeviceModel.monitor_status == MONITORED)
            .group_by(KnownDeviceModel.customer_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {customer_id: total for customer_id, total in rows}

    async def list_pending(self) -> list[KnownDevice]:
        stmt = (
            select(KnownDeviceModel, CustomerConfigModel.name)
            .join(
                CustomerConfigModel,
                CustomerConfigModel.customer_id == KnownDeviceModel.customer_id,
            )
            .where(*_pending_filters())
            .order_by(KnownDeviceModel.first_seen_at.desc(), KnownDeviceModel.device_id.desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [_to_entity(device, customer_name) for device, customer_name in rows]

    async def count_pending(self) -> int:
        stmt = (
            select(func.count())
            .select_from(KnownDeviceModel)
            .join(
                CustomerConfigModel,
                CustomerConfigModel.customer_id == KnownDeviceModel.customer_id,
            )
            .where(*_pending_filters(), KnownDeviceModel.dismissed.is_(False))
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def set_dismissed(self, device_id: int, dismissed: bool) -> bool:
        stmt = (
            update(KnownDeviceModel)
            .where(KnownDeviceModel.device_id == device_id)
            .values(dismissed=dismissed, updated_at=func.now())
            .returning(KnownDeviceModel.device_id)
        )
        return (await self._session.execute(stmt)).scalars().first() is not None

    async def upsert(self, entries: Sequence[DeviceInventoryEntry]) -> list[int]:
        if not entries:
            return []
        known = await self._existing_ids([entry.device_id for entry in entries])
        for batch in batched(entries, BATCH_ROWS):
            stmt = insert(KnownDeviceModel).values([asdict(entry) for entry in batch])
            await self._session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[KnownDeviceModel.device_id], set_=_refresh_values(stmt)
                )
            )
        return [entry.device_id for entry in entries if entry.device_id not in known]

    async def prune_missing(
        self, customer_id: int, present_device_ids: Sequence[int]
    ) -> int:
        stmt = (
            delete(KnownDeviceModel)
            .where(
                KnownDeviceModel.customer_id == customer_id,
                KnownDeviceModel.device_id.not_in(present_device_ids),
            )
            .returning(KnownDeviceModel.device_id)
        )
        return len((await self._session.execute(stmt)).scalars().all())

    async def list_offline(self, older_than_hours: int) -> list[OfflineDevice]:
        cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
        # LEFT JOIN — no filtra por CustomerConfigModel.enabled (caso Santander).
        # monitor_status == 'Y' sí filtra (equivalente al legacy, ver
        # sds_autoloader/db/devices.py::list_offline_devices): un equipo dado de baja del
        # monitoreo en SDS (X/J/I) ya no genera avisos de offline ni ensucia la detección
        # de caídas masivas, aunque su fila siga en known_devices con last_contact viejo.
        stmt = (
            select(KnownDeviceModel, CustomerConfigModel.name)
            .outerjoin(
                CustomerConfigModel,
                CustomerConfigModel.customer_id == KnownDeviceModel.customer_id,
            )
            .where(
                KnownDeviceModel.monitor_status == MONITORED,
                KnownDeviceModel.last_contact.isnot(None),
                KnownDeviceModel.last_contact < cutoff,
            )
            .order_by(KnownDeviceModel.last_contact.asc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [_to_offline_device(device, customer_name) for device, customer_name in rows]

    async def set_device_locations(
        self, entries: Sequence[DeviceLocationUpdate]
    ) -> None:
        if not entries:
            return
        for entry in entries:
            stmt = (
                update(KnownDeviceModel)
                .where(KnownDeviceModel.device_id == entry.device_id)
                .values(
                    cd_status=entry.cd_status,
                    cd_detail=entry.cd_detail,
                    cd_checked_at=func.now(),
                    updated_at=func.now(),
                )
            )
            await self._session.execute(stmt)

    async def set_offline_dismissed(self, device_id: int, dismissed: bool) -> bool:
        stmt = (
            update(KnownDeviceModel)
            .where(KnownDeviceModel.device_id == device_id)
            .values(offline_dismissed=dismissed, updated_at=func.now())
            .returning(KnownDeviceModel.device_id)
        )
        return (await self._session.execute(stmt)).scalars().first() is not None

    async def delete_device(self, device_id: int) -> bool:
        stmt = (
            delete(KnownDeviceModel)
            .where(KnownDeviceModel.device_id == device_id)
            .returning(KnownDeviceModel.device_id)
        )
        return (await self._session.execute(stmt)).scalars().first() is not None

    async def _existing_ids(self, device_ids: Sequence[int]) -> set[int]:
        known: set[int] = set()
        for batch in batched(device_ids, BATCH_ROWS):
            stmt = select(KnownDeviceModel.device_id).where(
                KnownDeviceModel.device_id.in_(batch)
            )
            known.update((await self._session.execute(stmt)).scalars().all())
        return known


def _pending_filters() -> tuple[ColumnElement[bool], ...]:
    return (
        KnownDeviceModel.monitor_status.not_in(MONITORED_STATUSES),
        CustomerConfigModel.enabled.is_(True),
    )


def _refresh_values(stmt: Insert) -> dict[str, object]:
    """Pisa el estado actual del equipo y, si volvió a reportar (cambió last_contact),
    limpia el veredicto de la auditoría de offline, que quedó obsoleto."""
    excluded = stmt.excluded
    contact_changed = KnownDeviceModel.last_contact.is_distinct_from(excluded.last_contact)
    return {
        "customer_id": excluded.customer_id,
        "serial": excluded.serial,
        "model": excluded.model,
        "zone": excluded.zone,
        "ip_address": excluded.ip_address,
        "monitor_status": excluded.monitor_status,
        "monitor_name": excluded.monitor_name,
        "discovery_date": excluded.discovery_date,
        "last_contact": excluded.last_contact,
        "updated_at": func.now(),
        "cd_status": _cleared_if(contact_changed, KnownDeviceModel.cd_status, ""),
        "cd_detail": _cleared_if(contact_changed, KnownDeviceModel.cd_detail, ""),
        "cd_checked_at": _cleared_if(contact_changed, KnownDeviceModel.cd_checked_at, None),
    }


def _cleared_if(
    condition: ColumnElement[bool], column: object, empty: object
) -> ColumnElement[object]:
    return case((condition, empty), else_=column)


def _to_offline_device(row: KnownDeviceModel, customer_name: str | None) -> OfflineDevice:
    return OfflineDevice(
        device_id=row.device_id,
        customer_id=row.customer_id,
        customer_name=customer_name or "",
        serial=row.serial,
        model=row.model,
        zone=row.zone,
        last_contact=row.last_contact,
        monitor_name=row.monitor_name,
        cd_status=row.cd_status,
        cd_detail=row.cd_detail,
        cd_checked_at=row.cd_checked_at,
        offline_dismissed=row.offline_dismissed,
    )


def _to_entity(row: KnownDeviceModel, customer_name: str) -> KnownDevice:
    return KnownDevice(
        device_id=row.device_id,
        customer_id=row.customer_id,
        customer_name=customer_name,
        serial=row.serial,
        model=row.model,
        zone=row.zone,
        ip_address=row.ip_address,
        monitor_status=row.monitor_status,
        discovery_date=row.discovery_date,
        last_contact=row.last_contact,
        first_seen_at=row.first_seen_at,
        dismissed=row.dismissed,
    )
