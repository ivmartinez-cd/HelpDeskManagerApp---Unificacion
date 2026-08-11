"""Caso de uso SyncNewDevices — port de POST /api/sync-new-devices + device_sync.py.

Insight no ofrece notificaciones de descubrimiento, así que la única forma de detectar
equipos nuevos es traer el inventario completo de cada cliente y diffearlo contra
known_devices.

Dos reglas que vienen de producción y no son cosméticas:

- Los equipos sin número de serie se descartan: son ruido del discovery (IPs que no
  respondieron identificación) y sin serie no hay forma de registrarlos en SDS.
- Se podan los equipos que Insight ya no devuelve para un cliente (dados de baja por
  fuera de esta app). El upsert nunca borra, así que sin esto quedaban huérfanos en
  Equipos Offline para siempre — medido el 2026-07-31. La poda corre SOLO con el fetch
  completo y exitoso de ese cliente: un error transitorio de red no puede borrar
  equipos válidos.
"""

import asyncio
import logging
from dataclasses import dataclass

from src.modules.insumos.application.use_cases._device_inventory_parsing import (
    to_customer,
    to_inventory_entry,
)
from src.modules.insumos.domain.entities.known_device import DeviceInventoryEntry
from src.modules.insumos.domain.repositories.customer_config_repository import (
    CustomerConfigRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import (
    InsightGateway,
    JsonDict,
)
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

# El fetch por cliente es liviano; el tope evita abrir ~56 conexiones simultáneas
# contra Insight y desplazar a la UI (el legacy usaba 8 hilos por el mismo motivo).
MAX_CONCURRENT_FETCHES = 8


@dataclass(frozen=True)
class SyncNewDevicesPorts:
    insight: InsightGateway
    customers: CustomerConfigRepository
    devices: KnownDeviceRepository


@dataclass(frozen=True)
class SyncNewDevicesResult:
    new_device_ids: list[int]
    pruned: int


class SyncNewDevices:
    def __init__(self, ports: SyncNewDevicesPorts) -> None:
        self._ports = ports

    async def execute(self) -> SyncNewDevicesResult:
        customers = await self._fetch_customers()
        await self._ports.customers.sync_discovered([to_customer(c) for c in customers])
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)
        fetched = await asyncio.gather(
            *(self._fetch_devices(c, semaphore) for c in customers)
        )
        entries: list[DeviceInventoryEntry] = []
        pruned = 0
        for customer_id, devices in fetched:
            if devices is None:
                continue
            pruned += await self._prune(customer_id, devices)
            entries.extend(_valid_entries(customer_id, devices))
        return SyncNewDevicesResult(
            new_device_ids=await self._ports.devices.upsert(entries), pruned=pruned
        )

    async def _fetch_customers(self) -> list[JsonDict]:
        """Sin el padrón no hay a quién pedirle equipos: acá sí se corta el sync."""
        try:
            return await self._ports.insight.get_customers()
        except Exception as exc:
            logger.exception("sync_new_devices: Insight no devolvió el padrón de clientes")
            raise ExternalServiceError(
                "No se pudo sincronizar con la Insight API"
            ) from exc

    async def _fetch_devices(
        self, customer: JsonDict, semaphore: asyncio.Semaphore
    ) -> tuple[int, list[JsonDict] | None]:
        """None = el fetch falló. Un cliente caído no aborta el resto (se detecta en el
        próximo ciclo) pero sí desactiva la poda de ESE cliente."""
        customer_id = int(customer["customerId"])
        async with semaphore:
            try:
                return customer_id, await self._ports.insight.get_devices(customer_id)
            except Exception as exc:
                logger.warning(
                    "sync_new_devices: error al traer equipos del cliente",
                    extra={"customer_id": customer_id, "customer": customer.get("name")},
                    exc_info=exc,
                )
                return customer_id, None

    async def _prune(self, customer_id: int, devices: list[JsonDict]) -> int:
        present = [int(device["deviceId"]) for device in devices]
        pruned = await self._ports.devices.prune_missing(customer_id, present)
        if pruned:
            logger.info(
                "sync_new_devices: equipos podados de known_devices (ya no en Insight)",
                extra={"customer_id": customer_id, "pruned": pruned},
            )
        return pruned


def _valid_entries(customer_id: int, devices: list[JsonDict]) -> list[DeviceInventoryEntry]:
    entries = (to_inventory_entry(customer_id, device) for device in devices)
    return [entry for entry in entries if entry.serial]
