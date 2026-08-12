"""Tests de integración de SqlAlchemyKnownDeviceRepository.list_offline contra el
Postgres de test.

Cubre la regresión real (2026-08-12): el port no filtraba por monitor_status='Y' como
sí hace el legacy (sds_autoloader/db/devices.py::list_offline_devices), así que equipos
ya dados de baja del monitoreo en SDS pero con una fila vieja en known_devices inflaban
la detección de equipos offline y de caídas masivas de colector.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.known_device import DeviceInventoryEntry
from src.modules.insumos.infrastructure.repositories.sqlalchemy_known_device_repository import (
    SqlAlchemyKnownDeviceRepository,
)

_OLD_CONTACT = datetime.now(UTC) - timedelta(hours=200)
_RECENT_CONTACT = datetime.now(UTC) - timedelta(hours=1)


def _entry(device_id: int, **overrides: object) -> DeviceInventoryEntry:
    base: dict[str, object] = {
        "device_id": device_id,
        "customer_id": 1,
        "serial": f"SERIE{device_id}",
        "model": "LaserJet",
        "zone": "Zona 1",
        "ip_address": "10.0.0.1",
        "monitor_status": "Y",
        "monitor_name": "colector-1",
        "discovery_date": None,
        "last_contact": _OLD_CONTACT,
    }
    base.update(overrides)
    return DeviceInventoryEntry(**base)  # type: ignore[arg-type]


async def test_list_offline_excluye_equipos_dados_de_baja_del_monitoreo(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyKnownDeviceRepository(db_session)
    await repo.upsert(
        [
            _entry(1, monitor_status="Y"),
            _entry(2, monitor_status="X"),
            _entry(3, monitor_status="J"),
            _entry(4, monitor_status="I"),
        ]
    )

    offline = await repo.list_offline(older_than_hours=72)

    assert [d.device_id for d in offline] == [1]


async def test_list_offline_excluye_equipos_con_contacto_reciente(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyKnownDeviceRepository(db_session)
    await repo.upsert(
        [
            _entry(1, monitor_status="Y", last_contact=_OLD_CONTACT),
            _entry(2, monitor_status="Y", last_contact=_RECENT_CONTACT),
        ]
    )

    offline = await repo.list_offline(older_than_hours=72)

    assert [d.device_id for d in offline] == [1]


async def test_list_offline_incluye_clientes_sin_customers_config(
    db_session: AsyncSession,
) -> None:
    """LEFT JOIN deliberado (caso Santander): un equipo offline de un cliente sin fila
    en customers_config, o con enabled=False, igual tiene que aparecer en la auditoría."""
    repo = SqlAlchemyKnownDeviceRepository(db_session)
    await repo.upsert([_entry(1, customer_id=999, monitor_status="Y")])

    offline = await repo.list_offline(older_than_hours=72)

    assert [d.device_id for d in offline] == [1]
    assert offline[0].customer_name == ""
