"""Traducción de los dicts crudos de Insight a entradas de inventario.

Vive en application y no en el gateway porque las claves camelCase del wire son el
contrato de Insight, no del dominio (mismo criterio que el resto del módulo).
"""

from datetime import datetime

from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.domain.entities.known_device import DeviceInventoryEntry
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.value_objects.insight_datetime import parse_insight_utc
from src.modules.insumos.domain.value_objects.serial_number import clean_serial


def to_customer(raw: JsonDict) -> CustomerConfig:
    """`enabled` real lo decide el padrón; acá solo viaja el default de un alta."""
    return CustomerConfig(
        customer_id=int(raw["customerId"]), name=str(raw.get("name") or ""), enabled=False
    )


def to_inventory_entry(customer_id: int, device: JsonDict) -> DeviceInventoryEntry:
    extended = device.get("extendedFields") or {}
    return DeviceInventoryEntry(
        device_id=int(device["deviceId"]),
        customer_id=customer_id,
        serial=clean_serial(device.get("serialNumber") or ""),
        model=str(extended.get("model") or ""),
        zone=str(extended.get("zone") or ""),
        ip_address=str(device.get("ipAddress") or ""),
        monitor_status=str(device.get("monitorStatus") or ""),
        monitor_name=str(extended.get("monitorName") or ""),
        discovery_date=_parsed(device.get("discoveryDate")),
        last_contact=_parsed(device.get("lastContact")),
    )


def _parsed(raw: object) -> datetime | None:
    return parse_insight_utc(raw) if isinstance(raw, str) else None
