"""Lógica de importación de contactos por zona desde el PortalWeb de SDS.

Portado de `zone_contact_import.py` del legacy SDSInsumos. La diferencia principal
es que usa asyncio.gather en lugar de ThreadPoolExecutor (parallel_map del legacy).
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.zone_contacts import (
    ZoneContactPreviewRow,
    ZoneContactRow,
)

logger = logging.getLogger(__name__)


class ZoneImportInsightPort(Protocol):
    async def get_devices(self, customer_id: int) -> list[dict]: ...  # type: ignore[type-arg]
    async def get_zones(self, customer_id: int) -> list[dict]: ...  # type: ignore[type-arg]


class ZoneImportPortalPort(Protocol):
    async def ensure_login(self) -> None: ...

    async def get_delivery_location_contact(
        self, customer_id: int, location_id: int
    ) -> ContactInfo | None: ...


def _zone_id_to_raw_zones(devices: list[dict]) -> dict[int, set[str]]:  # type: ignore[type-arg]
    """zoneId → variantes de "zone" vistas en los equipos del cliente."""
    result: dict[int, set[str]] = {}
    for d in devices:
        ef = d.get("extendedFields") or {}
        zone_id = ef.get("zoneId")
        zone = ef.get("zone")
        if zone_id is None or not zone:
            continue
        result.setdefault(zone_id, set()).add(zone)
    return result


_NO_LOCATION_ERROR = "Sin ubicación de entrega vinculada en Insight"


@dataclass(frozen=True)
class _ZoneLookupContext:
    """Lo que comparten todos los lookups paralelos de un mismo cliente."""

    customer_id: int
    portal: ZoneImportPortalPort
    zone_by_id: dict[int, dict]  # type: ignore[type-arg]
    existing_by_zone: dict[str, ZoneContactRow]


def _preview_row(
    zone: str, contact: ContactInfo, current: ZoneContactRow | None
) -> ZoneContactPreviewRow:
    return ZoneContactPreviewRow(
        zone=zone,
        apellido=contact.apellido,
        nombre=contact.nombre,
        email=contact.email,
        telefono=contact.telefono,
        already_configured=current is not None,
        current_apellido=current.dest_apellido if current else "",
        current_nombre=current.dest_nombre if current else "",
        current_email=current.dest_email if current else "",
        current_telefono=current.dest_telefono if current else "",
    )


async def _lookup_zone(
    ctx: _ZoneLookupContext, zone_id: int, raw_zones: set[str]
) -> list[ZoneContactPreviewRow]:
    """Filas de vista previa para todas las variantes de "zone" de un zoneId."""
    zone_meta = ctx.zone_by_id.get(zone_id)
    location_id = zone_meta.get("deliveryLocationId") if zone_meta else None
    if not location_id:
        return [ZoneContactPreviewRow(zone=z, error=_NO_LOCATION_ERROR) for z in raw_zones]
    try:
        contact = await ctx.portal.get_delivery_location_contact(ctx.customer_id, location_id)
    except Exception as exc:
        logger.warning(
            "zone-contacts-import: cliente %s zoneId=%s: %s",
            ctx.customer_id, zone_id, exc,
            exc_info=exc,
        )
        return [ZoneContactPreviewRow(zone=z, error=str(exc)) for z in raw_zones]
    if contact is None:
        return []
    return [_preview_row(z, contact, ctx.existing_by_zone.get(z)) for z in raw_zones]


async def _lookup_all(
    ctx: _ZoneLookupContext, zone_id_to_raw: dict[int, set[str]]
) -> list[ZoneContactPreviewRow]:
    """Scrapea las delivery locations en paralelo (asyncio.gather) — nunca secuencial."""
    tasks = [_lookup_zone(ctx, zid, rzones) for zid, rzones in zone_id_to_raw.items()]
    nested = await asyncio.gather(*tasks)
    rows = [r for sublist in nested for r in sublist]
    rows.sort(key=lambda r: r.zone)
    return rows


async def preview_zone_contacts(
    customer_id: int,
    insight: ZoneImportInsightPort,
    portal: ZoneImportPortalPort,
    existing_by_zone: dict[str, ZoneContactRow],
) -> list[ZoneContactPreviewRow]:
    """Vista previa de los contactos que se importarían, sin escribir."""
    devices = await insight.get_devices(customer_id)
    zone_id_to_raw = _zone_id_to_raw_zones(devices)
    if not zone_id_to_raw:
        return []
    zones_raw = await insight.get_zones(customer_id)
    ctx = _ZoneLookupContext(
        customer_id, portal, {z["zoneId"]: z for z in zones_raw}, existing_by_zone
    )
    await portal.ensure_login()
    return await _lookup_all(ctx, zone_id_to_raw)


def contact_to_zone_row(
    zone: str,
    contact: ContactInfo,
    observaciones: str = "",
) -> ZoneContactRow:
    """Convierte un ContactInfo de SDS (apellido=nombre completo) a ZoneContactRow.

    Solicitante = Destinatario — convención validada en la migración piloto
    (ver docs/MIGRACION_CONTACTOS_SDS.md).
    """
    return ZoneContactRow(
        zone=zone,
        sol_apellido=contact.apellido,
        sol_nombre=contact.nombre,
        sol_telefono=contact.telefono,
        sol_email=contact.email,
        sol_sector="",
        dest_apellido=contact.apellido,
        dest_nombre=contact.nombre,
        dest_telefono=contact.telefono,
        dest_email=contact.email,
        dest_sector="",
        observaciones=observaciones,
    )


