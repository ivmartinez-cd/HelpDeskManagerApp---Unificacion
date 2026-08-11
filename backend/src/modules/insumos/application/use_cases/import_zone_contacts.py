"""Casos de uso de importación de contactos por zona desde Insight y el PortalWeb."""

import asyncio
import logging
from dataclasses import dataclass

from src.modules.insumos.domain.repositories.zone_contact_repository import ZoneContactRepository
from src.modules.insumos.domain.services.sds_contact_parser import parse_sds_contact_comment
from src.modules.insumos.domain.services.zone_contact_import import (
    ZoneImportInsightPort,
    ZoneImportPortalPort,
    contact_to_zone_row,
    preview_zone_contacts,
)
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.zone_contacts import (
    SdsContactRow,
    ZoneContactPreviewRow,
    ZoneContactRow,
    ZoneOverwriteRequest,
)
from src.modules.insumos.infrastructure.insight.httpx_insight_gateway import HttpxInsightGateway
from src.modules.insumos.infrastructure.soap.zeep_wsayc_gateway import ZeepWsAycGateway
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass
class ZoneContactImportPorts:
    zone_contacts: ZoneContactRepository
    insight: ZoneImportInsightPort
    portal: ZoneImportPortalPort


class PreviewZoneContactsImport:
    def __init__(self, ports: ZoneContactImportPorts) -> None:
        self._ports = ports

    async def execute(self, customer_id: int) -> list[ZoneContactPreviewRow]:
        existing_rows = await self._ports.zone_contacts.list_all(customer_id)
        existing_by_zone = {r.zone: r for r in existing_rows}
        return await preview_zone_contacts(
            customer_id, self._ports.insight, self._ports.portal, existing_by_zone
        )


class ApplyZoneContactsImport:
    def __init__(self, ports: ZoneContactImportPorts) -> None:
        self._ports = ports

    async def execute(
        self, customer_id: int, requested: list[ZoneOverwriteRequest]
    ) -> int:
        existing_rows = await self._ports.zone_contacts.list_all(customer_id)
        existing_by_zone = {r.zone: r for r in existing_rows}
        fresh_rows = await preview_zone_contacts(
            customer_id, self._ports.insight, self._ports.portal, existing_by_zone
        )
        fresh_by_zone = {r.zone: r for r in fresh_rows}
        applied = 0
        for req in requested:
            row = fresh_by_zone.get(req.zone)
            if row is None or row.error or not row.apellido:
                continue
            if row.already_configured and not req.overwrite:
                continue
            current = existing_by_zone.get(row.zone)
            observaciones = current.observaciones if current else ""
            contact = ContactInfo(
                apellido=row.apellido,
                nombre=row.nombre,
                telefono=row.telefono,
                email=row.email,
            )
            zone_row = contact_to_zone_row(row.zone, contact, observaciones)
            await self._ports.zone_contacts.upsert(customer_id, zone_row)
            applied += 1
        return applied


class GetSdsContacts:
    """Contactos detectados en el comentario libre de cada equipo de un cliente."""

    def __init__(self, insight: HttpxInsightGateway) -> None:
        self._insight = insight

    async def execute(self, customer_id: int) -> list[SdsContactRow]:
        try:
            devices = await self._insight.get_devices(customer_id)
        except Exception as exc:
            logger.error(
                "GetSdsContacts: error obteniendo equipos del cliente %s",
                customer_id,
                extra={"customer_id": customer_id},
                exc_info=exc,
            )
            raise ExternalServiceError(
                "No se pudieron obtener los equipos desde Insight"
            ) from exc
        seen: set[tuple] = set()  # type: ignore[type-arg]
        rows: list[SdsContactRow] = []
        for d in devices:
            ef = d.get("extendedFields") or {}
            zone = (ef.get("zone") or "").strip()
            parsed = parse_sds_contact_comment(zone, ef.get("comment"))
            if parsed is None:
                continue
            key = (parsed.zone, parsed.contacto, parsed.email, parsed.sucursal)
            if key not in seen:
                seen.add(key)
                rows.append(parsed)
        rows.sort(key=lambda r: (r.zone, r.contacto))
        return rows


class GetCustomerZones:
    """Zonas distintas del cliente según sus solicitudes activas en Insight."""

    def __init__(self, insight: HttpxInsightGateway) -> None:
        self._insight = insight

    async def execute(self, customer_id: int) -> list[str]:
        try:
            requests = await self._insight.get_consumable_requests(
                customer_id, workflow_status="OUTSTANDING"
            )
            device_ids = list({req["deviceId"] for req in requests})
            devices = await asyncio.gather(
                *[self._insight.get_device_by_id(did) for did in device_ids],
                return_exceptions=True,
            )
        except Exception as exc:
            logger.error(
                "GetCustomerZones: error obteniendo zonas del cliente %s",
                customer_id,
                extra={"customer_id": customer_id},
                exc_info=exc,
            )
            raise ExternalServiceError(
                "No se pudieron obtener zonas desde Insight"
            ) from exc
        zones: set[str] = set()
        for d in devices:
            if isinstance(d, BaseException):
                continue
            zone = (d.get("extendedFields") or {}).get("zone", "")
            if zone:
                zones.add(zone)
        return sorted(zones)


class ImportContactsFromSupply:
    """Importa contactos de un supply de wsAyC a la zona del cliente."""

    def __init__(self, wsayc: ZeepWsAycGateway, repo: ZoneContactRepository) -> None:
        self._wsayc = wsayc
        self._repo = repo

    async def execute(
        self, customer_id: int, supply_id: int
    ) -> ZoneContactRow | None:
        supply = await self._wsayc.fetch_supply_by_id(supply_id)
        if supply is None:
            return None
        zone = supply.sucursal.strip()
        sector = supply.sector.strip()
        row = ZoneContactRow(
            zone=zone,
            sol_apellido=supply.solicitante_nombre.strip(),
            sol_nombre="",
            sol_telefono=supply.solicitante_telefono.strip(),
            sol_email=supply.solicitante_email.strip(),
            sol_sector=sector,
            dest_apellido=supply.destinatario_nombre.strip(),
            dest_nombre="",
            dest_telefono=supply.destinatario_telefono.strip(),
            dest_email=supply.destinatario_email.strip(),
            dest_sector=sector,
        )
        await self._repo.upsert(customer_id, row)
        return row
