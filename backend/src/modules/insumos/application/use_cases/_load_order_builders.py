"""Funciones de soporte del caso de uso LoadOrder — separadas por límite de tamaño (guía §4)."""

import logging

from src.modules.insumos.application.dtos.load_order import (
    LoadOrderCommand,
    LoadOrderResult,
    ResolvedRequest,
    failure,
)
from src.modules.insumos.application.use_cases._load_order_context import (
    LoadOrderConfig,
    LoadOrderPorts,
)
from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    ORDER_TYPE_SUPPLY,
    AuditRecord,
)
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.services.maintenance_kit import is_maintenance_kit
from src.modules.insumos.domain.services.stale_replacement import is_stale_replaced
from src.modules.insumos.domain.services.zone_delivery_notice import SucursalOverride
from src.modules.insumos.domain.value_objects.incident_request import IncidentRequest
from src.modules.insumos.domain.value_objects.insight_datetime import parse_insight_utc
from src.modules.insumos.domain.value_objects.order_reference import order_reference
from src.modules.insumos.domain.value_objects.order_request import (
    ContactInfo,
    OrderLine,
    OrderRequest,
)
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContacts

logger = logging.getLogger(__name__)


async def resolve_from_insight(
    ports: LoadOrderPorts, command: LoadOrderCommand
) -> ResolvedRequest | LoadOrderResult:
    """Re-deriva todo del servidor contra Insight; nunca confía en el body."""
    try:
        requests = await ports.insight.get_consumable_requests(
            command.customer_id, workflow_status="OUTSTANDING"
        )
    except Exception as exc:
        logger.error(
            "No se pudo verificar la solicitud %s contra Insight",
            command.hp_request_id,
            exc_info=exc,
        )
        return failure("No se pudo verificar la solicitud contra Insight. Intentá de nuevo.")
    matched = next((r for r in requests if r.get("id") == command.hp_request_id), None)
    if matched is None:
        return failure(
            "La solicitud no existe o ya no está pendiente en Insight para este cliente."
        )
    if is_stale_replaced(matched.get("requested"), matched.get("replacedDate")):
        return failure(
            "El consumible ya fue reemplazado (SDS no cerró la alerta vieja); "
            "no hace falta cargar este pedido."
        )
    return await resolve_device_from_match(ports.insight, command, matched)


async def resolve_device_from_match(
    insight: InsightGateway, command: LoadOrderCommand, matched: JsonDict
) -> ResolvedRequest | LoadOrderResult:
    device_id = int(matched["deviceId"])
    device = await insight.get_device_by_id(device_id)
    device_serial = str(device.get("serialNumber") or "")
    if not device_serial:
        logger.warning(
            "load_order: request %s (deviceId=%s) sin número de serie en Insight",
            command.hp_request_id,
            device_id,
        )
        return failure("No se pudo determinar el número de serie del equipo desde Insight.")
    consumable = matched.get("consumable") or {}
    reorder_part = consumable.get("reorderPart") or {}
    return ResolvedRequest(
        hp_request_id=command.hp_request_id,
        device_id=device_id,
        device_serial=device_serial,
        store_name=str((device.get("extendedFields") or {}).get("zone") or ""),
        sku=str(consumable.get("sku") or ""),
        description=str(consumable.get("description") or ""),
        percent_left=consumable.get("percentLeft"),
        days_left=consumable.get("daysLeft"),
        pages_left=consumable.get("pagesLeft"),
        requested=matched.get("requested"),
        is_maintenance_kit=is_maintenance_kit(
            str(consumable.get("description") or ""), str(reorder_part.get("type") or "")
        ),
        warn=_consumable_warn(consumable),
    )


async def update_insight_on_success(
    insight: InsightGateway,
    config: LoadOrderConfig,
    command: LoadOrderCommand,
    order_id: str,
) -> None:
    """Marca la solicitud como atendida en Insight. Fallo no revierte el pedido en CD."""
    try:
        await insight.update_consumable_request(
            request_id=command.hp_request_id,
            external_ref=f"CD-{order_id}",
            status_update=config.insight_status_on_order,
            comment=f"Pedido creado en Canal Directo: {order_id}",
        )
        logger.info(
            "Insight request %s marcada como %s (ref CD-%s)",
            command.hp_request_id,
            config.insight_status_on_order,
            order_id,
        )
    except Exception as exc:
        logger.error(
            "No se pudo actualizar Insight para request %s (pedido %s ya creado en CD)",
            command.hp_request_id,
            order_id,
            exc_info=exc,
        )


def build_order_request(
    command: LoadOrderCommand, resolved: ResolvedRequest, zona: ZoneContacts | None
) -> OrderRequest:
    solicitante, destinatario = _order_contacts(zona)
    return OrderRequest(
        customer_id=command.customer_id,
        customer_name=command.customer_name,
        store_name=resolved.store_name,
        device_serial=resolved.device_serial,
        lines=(OrderLine(sku=resolved.sku, quantity=1, description=resolved.description),),
        reference=order_reference(command.hp_request_id),
        solicitante=solicitante,
        destinatario=destinatario,
        detalle=build_detalle(resolved, zona.observaciones if zona else ""),
        override_insumo_id=command.override_insumo_id,
        revision=command.revision,
    )


def build_incident_request(
    command: LoadOrderCommand, resolved: ResolvedRequest, zona: ZoneContacts | None
) -> IncidentRequest:
    solicitante, destinatario = _order_contacts(zona)
    return IncidentRequest(
        device_serial=resolved.device_serial,
        reference=order_reference(command.hp_request_id),
        falla=f"Kit de mantenimiento solicitado por SDS: {resolved.description}"
        if resolved.description
        else "Kit de mantenimiento (solicitud SDS)",
        origen_id="",  # "" = usar el default de CanalDirectoOrderSettings
        solicitante=solicitante,
        destinatario=destinatario,
    )


def build_detalle(resolved: ResolvedRequest, observaciones: str) -> str:
    parts = []
    if resolved.percent_left is not None:
        value = float(resolved.percent_left)
        parts.append(f"le queda {int(value) if value.is_integer() else value}%")
    if resolved.pages_left is not None:
        parts.append(f"({resolved.pages_left} pág. rest.)")
    if resolved.days_left is not None:
        parts.append(f"para consumirse en {resolved.days_left} días")
    detalle = " ".join(parts)
    if observaciones.strip():
        detalle = f"{observaciones.strip()} {detalle}".strip()
    return detalle


def compose_audit_detail(base: str | None, zone_override: SucursalOverride) -> str | None:
    """Detail del audit CREATED: lo que ya traía el caller (swap_note, "Pre-Correctivo
    (kit de mantenimiento)") más el aviso de cambio de sucursal si corresponde — única
    constancia visible en el Historial cuando el pedido se creó sin que nadie viera el
    modal recordatorio (ej. auto-carga)."""
    parts = [base] if base else []
    if zone_override.requiere_cambio:
        parts.append(
            f"Pendiente cambio de sucursal a {zone_override.sucursal}"
            if zone_override.sucursal
            else "Pendiente cambio de sucursal (ver observación de zona)"
        )
    return " · ".join(parts) or None


def build_processed_request(
    command: LoadOrderCommand, resolved: ResolvedRequest, order_id: str
) -> ProcessedRequest:
    return ProcessedRequest(
        hp_request_id=command.hp_request_id,
        device_id=resolved.device_id,
        device_serial=resolved.device_serial,
        customer_id=command.customer_id,
        sku=resolved.sku,
        internal_order_id=order_id,
        description=resolved.description,
        initial_percent_left=rounded(resolved.percent_left),
        initial_days_left=resolved.days_left,
        initial_pages_left=resolved.pages_left,
    )


def build_audit_created(
    command: LoadOrderCommand,
    resolved: ResolvedRequest,
    order_id: str,
    detail: str | None,
    order_type: str = ORDER_TYPE_SUPPLY,
) -> AuditRecord:
    return AuditRecord(
        event=EVENT_CREATED,
        hp_request_id=command.hp_request_id,
        customer_id=command.customer_id,
        customer_name=command.customer_name,
        device_serial=resolved.device_serial,
        sku=resolved.sku,
        internal_order_id=order_id,
        detail=detail,
        dry_run=command.dry_run,
        hp_request_time=parse_insight_utc(resolved.requested),
        description=resolved.description,
        device_id=resolved.device_id,
        order_type=order_type,
        initial_percent_left=rounded(resolved.percent_left),
        initial_days_left=resolved.days_left,
        initial_pages_left=resolved.pages_left,
    )


def build_audit_failed(
    command: LoadOrderCommand, resolved: ResolvedRequest, detail: str
) -> AuditRecord:
    return AuditRecord(
        event=EVENT_FAILED,
        hp_request_id=command.hp_request_id,
        customer_id=command.customer_id,
        customer_name=command.customer_name,
        device_serial=resolved.device_serial,
        sku=resolved.sku,
        detail=detail,
        dry_run=command.dry_run,
        hp_request_time=parse_insight_utc(resolved.requested),
        description=resolved.description,
    )


def rounded(value: float | None) -> int | None:
    return round(value) if value is not None else None


def _consumable_warn(consumable: JsonDict) -> str | None:
    if consumable.get("percentLeft") is None or consumable.get("daysLeft") is None:
        return (
            "No se pudo obtener el nivel de consumible; el pedido se creó sin esa información."
        )
    return None


def _order_contacts(zona: ZoneContacts | None) -> tuple[ContactInfo | None, ContactInfo | None]:
    """Solo se usa el contacto per-zona si tiene al menos nombre o apellido."""
    if zona is None:
        return None, None
    sol = zona.solicitante
    dest = zona.destinatario
    solicitante = sol if (sol.apellido.strip() or sol.nombre.strip()) else None
    destinatario = dest if (dest.apellido.strip() or dest.nombre.strip()) else None
    return solicitante, destinatario
