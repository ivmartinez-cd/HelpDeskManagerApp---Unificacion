"""Caso de uso GetDeviceSupplies — port de GET /api/devices/{serial}/supplies
(routers/requests/query.py::get_device_supplies): últimos pedidos de insumos en Canal
Directo para una serie, combinando tres fuentes ordenadas por supply_id desc:

1. SOAP getTopSupplies (visible en el portal) — source="soap". El legacy barría todas
   las empresas de CD_EMPRESA_IDS; acá la empresa se resuelve por serie vía
   getMachineBySerial, igual que el resto del módulo (CanalDirectoSupplyLookup).
2. Cache local supply_serial_cache (scan incremental de pedidos de origen Interno) —
   source="local".
3. Pedidos creados por la app (processed_requests), por si son tan nuevos que todavía
   no aparecen en 1 ni 2 — source="local", reconfirmados en vivo por getSupplyById.

Con dry_run=True se loguea la llamada pero el flujo es idéntico (el SOAP es read-only).
"""

import asyncio
import logging
from dataclasses import dataclass

from src.modules.insumos.application.dtos.device_detail import (
    SOURCE_LOCAL,
    SOURCE_SOAP,
    DeviceSupplyRow,
)
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.value_objects.cd_datetime import (
    format_cd_datetime,
    parse_cd_datetime,
)
from src.modules.insumos.domain.value_objects.cd_state import PENDIENTE
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.domain.value_objects.serial_number import (
    clean_serial,
    serial_from_supply_fields,
)
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

logger = logging.getLogger(__name__)

# getTopSupplies trae los últimos N de la empresa entera; se pide de sobra porque
# después se filtra por serie (mismo criterio que el top=500 del legacy).
_PORTAL_TOP = "500"


@dataclass(frozen=True)
class GetDeviceSuppliesPorts:
    wsayc: WsAycGateway
    supply_cache: SupplyCacheRepository
    processed: ProcessedRequestRepository


class GetDeviceSupplies:
    def __init__(
        self, ports: GetDeviceSuppliesPorts, order_settings: CanalDirectoOrderSettings
    ) -> None:
        self._ports = ports
        self._settings = order_settings

    async def execute(
        self, device_serial: str, limit: int, dry_run: bool = False
    ) -> list[DeviceSupplyRow]:
        """Últimos `limit` pedidos de la serie, mergeados por supply_id (SOAP gana:
        tiene más campos) y con descripciones enriquecidas para los que quedaron sin."""
        serial = clean_serial(device_serial).upper()
        if dry_run:
            logger.info("[DRY RUN] get_device_supplies serial=%s", serial)
        own = await self._own_by_supply_id(serial)
        merged: dict[int, DeviceSupplyRow] = {}
        for row in await self._portal_rows(serial, own):
            merged.setdefault(row.supply_id, row)
        for row in await self._cache_rows(serial, limit, own):
            merged.setdefault(row.supply_id, row)
        await self._add_own_candidates(serial, own, merged)
        result = sorted(merged.values(), key=lambda r: r.supply_id, reverse=True)[:limit]
        await self._enrich_descriptions(result)
        return result

    async def _own_by_supply_id(self, serial: str) -> dict[int, ProcessedRequest]:
        """Pedidos propios (CREATED) por ID numérico — los DRYRUN y no parseables
        quedan afuera (no son supplies reales en CD)."""
        own: dict[int, ProcessedRequest] = {}
        for record in await self._ports.processed.get_created_by_serial(serial):
            try:
                own[int(record.internal_order_id.split("-")[0])] = record
            except (ValueError, IndexError):
                continue
        return own

    async def _portal_rows(
        self, serial: str, own: dict[int, ProcessedRequest]
    ) -> list[DeviceSupplyRow]:
        """Fuente 1: getTopSupplies de la empresa del equipo, filtrado por serie.
        Best-effort: el historial no puede caerse porque CD no responda — quedan las
        fuentes locales."""
        try:
            machine = await self._ports.wsayc.get_machine_by_serial(serial)
        except Exception as exc:
            logger.error(
                "get_device_supplies: getMachineBySerial falló para %s", serial, exc_info=exc
            )
            return []
        if machine is None or not machine.empresa_id:
            logger.warning(
                "get_device_supplies: %s sin empresa en CD; solo fuentes locales", serial
            )
            return []
        supplies = await self._ports.wsayc.get_supplies_for_empresa(
            machine.empresa_id, top=_PORTAL_TOP
        )
        rows = [self._portal_row(supply, serial, own) for supply in supplies]
        return [row for row in rows if row is not None]

    def _portal_row(
        self, supply: CdSupply, serial: str, own: dict[int, ProcessedRequest]
    ) -> DeviceSupplyRow | None:
        row_serial = serial_from_supply_fields(supply.nro_serie_solicitud, supply.nro_serie)
        if row_serial != serial or not supply.supply_id:
            return None
        # SKU/descripción propios como respaldo: el SOAP no siempre los trae, pero
        # nosotros sí los registramos al crear el pedido.
        own_record = own.get(supply.supply_id)
        return DeviceSupplyRow(
            supply_id=supply.supply_id,
            supply_id_full=supply_id_full(supply.supply_id),
            serial=row_serial,
            estado=supply.estado,
            fecha=supply.fecha,
            sku=supply.sku or (own_record.sku if own_record else ""),
            descripcion=supply.descripcion or (own_record.description if own_record else ""),
            supply_url=self._settings.supply_web_url(supply.supply_id),
            source=SOURCE_SOAP,
        )

    async def _cache_rows(
        self, serial: str, limit: int, own: dict[int, ProcessedRequest]
    ) -> list[DeviceSupplyRow]:
        """Fuente 2: cache local del scan incremental (todos los estados)."""
        entries = await self._ports.supply_cache.get_by_serial(serial, limit=limit * 3)
        return [self._cache_row(entry, own) for entry in entries]

    def _cache_row(
        self, entry: CachedSupply, own: dict[int, ProcessedRequest]
    ) -> DeviceSupplyRow:
        own_record = own.get(entry.supply_id)
        return DeviceSupplyRow(
            supply_id=entry.supply_id,
            supply_id_full=supply_id_full(entry.supply_id),
            serial=entry.serial,
            estado=entry.estado,
            fecha=format_cd_datetime(entry.fecha),
            sku=entry.sku or (own_record.sku if own_record else ""),
            descripcion=entry.description or (own_record.description if own_record else ""),
            supply_url=self._settings.supply_web_url(entry.supply_id),
            source=SOURCE_LOCAL,
        )

    async def _add_own_candidates(
        self, serial: str, own: dict[int, ProcessedRequest], merged: dict[int, DeviceSupplyRow]
    ) -> None:
        """Fuente 3: pedidos propios que no vinieron ni por SOAP ni por el cache —
        reconfirmados en vivo (por si la orden es muy nueva), en paralelo."""
        candidates = [(sid, record) for sid, record in own.items() if sid not in merged]
        if not candidates:
            return
        fresh = await asyncio.gather(
            *(self._ports.wsayc.fetch_supply_by_id(sid) for sid, _ in candidates)
        )
        updates: list[CachedSupply] = []
        for (sid, record), supply in zip(candidates, fresh, strict=True):
            merged[sid] = self._own_row(sid, record, supply, serial)
            if supply is not None:
                updates.append(
                    CachedSupply(
                        supply_id=sid,
                        serial=serial,
                        estado=supply.estado,
                        empresa_id=supply.empresa_id,
                        fecha=parse_cd_datetime(supply.fecha),
                    )
                )
        if updates:
            await self._ports.supply_cache.upsert(updates)

    def _own_row(
        self, sid: int, record: ProcessedRequest, supply: CdSupply | None, serial: str
    ) -> DeviceSupplyRow:
        """Si getSupplyById no lo vio (lag de lectura), estado Pendiente y la fecha de
        creación propia — nunca se lo esconde: la app lo creó, existe."""
        estado = supply.estado if supply is not None else PENDIENTE
        fecha = supply.fecha if supply is not None else format_cd_datetime(record.created_at)
        return DeviceSupplyRow(
            supply_id=sid,
            supply_id_full=supply_id_full(sid),
            serial=serial,
            estado=estado,
            fecha=fecha,
            sku=record.sku,
            descripcion=record.description,
            supply_url=self._settings.supply_web_url(sid),
            source=SOURCE_LOCAL,
        )

    async def _enrich_descriptions(self, result: list[DeviceSupplyRow]) -> None:
        """Pedidos de origen externo: ni el SOAP ni el cache traen el consumible real —
        el detalle del pedido es la única fuente. Solo para los que quedaron sin
        descripción y en paralelo; el gateway devuelve "" ante error (no bloquea)."""
        missing = [row for row in result if not row.descripcion]
        if not missing:
            return
        descriptions = await asyncio.gather(
            *(self._ports.wsayc.get_supply_description(row.supply_id) for row in missing)
        )
        updates: list[CachedSupply] = []
        for row, description in zip(missing, descriptions, strict=True):
            if not description:
                continue
            row.descripcion = description
            updates.append(
                CachedSupply(
                    supply_id=row.supply_id,
                    serial=row.serial,
                    estado=row.estado,
                    fecha=parse_cd_datetime(row.fecha),
                    description=description,
                )
            )
        if updates:
            await self._ports.supply_cache.upsert(updates)
