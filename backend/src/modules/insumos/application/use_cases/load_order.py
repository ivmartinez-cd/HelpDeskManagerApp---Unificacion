"""Caso de uso LoadOrder — el corazón del módulo (POST /api/requests/{id}/load).

Port del load_request del legacy: re-deriva TODO del lado del servidor contra Insight
(nunca confía en el body), corre los bloqueos 0-3 dentro del claim serie+sku y crea el
pedido (o el incidente, si es kit de mantenimiento) con la verificación post-creación
obligatoria. Responde siempre con un LoadOrderResult (el contrato "200 siempre" lo
serializa presentation).

Pendiente de pasos posteriores de la migración (explícito, no olvidado):
- request_alerts.resolve al crear (falta portar el módulo de alertas).
"""

import logging

from src.modules.insumos.application.dtos.load_order import (
    CONFLICT_AMBIGUOUS_INSUMO,
    LoadOrderCommand,
    LoadOrderResult,
    ResolvedRequest,
    failure,
    success,
)
from src.modules.insumos.application.use_cases._load_order_blockers import LoadOrderBlockers
from src.modules.insumos.application.use_cases._load_order_builders import (
    build_audit_created,
    build_audit_failed,
    build_incident_request,
    build_order_request,
    build_processed_request,
    compose_audit_detail,
    resolve_from_insight,
    update_insight_on_success,
)
from src.modules.insumos.application.use_cases._load_order_context import (
    LoadOrderConfig,
    LoadOrderPorts,
)
from src.modules.insumos.domain.entities.audit_record import ORDER_TYPE_INCIDENT
from src.modules.insumos.domain.errors import (
    InsumoAmbiguoError,
    InsumoNoConfiguradoError,
    OrderAlreadyInProgressError,
    SerieNoActivaEnCanalDirectoError,
)
from src.modules.insumos.domain.services.zone_delivery_notice import detect_sucursal_override
from src.modules.insumos.domain.value_objects.incident_request import IncidentRequest
from src.modules.insumos.domain.value_objects.order_request import OrderRequest
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContacts

logger = logging.getLogger(__name__)

_DRYRUN_PREFIX = "DRYRUN-"


class LoadOrder:
    def __init__(self, ports: LoadOrderPorts, config: LoadOrderConfig) -> None:
        self._ports = ports
        self._config = config
        self._blockers = LoadOrderBlockers(ports, config)

    async def execute(self, command: LoadOrderCommand) -> LoadOrderResult:
        resolved = await resolve_from_insight(self._ports, command)
        if isinstance(resolved, LoadOrderResult):
            return resolved

        async def guarded() -> LoadOrderResult:
            return await self._guarded_flow(command, resolved)

        try:
            return await self._ports.claimed_creation.run(
                device_serial=resolved.device_serial, sku=resolved.sku, action=guarded
            )
        except OrderAlreadyInProgressError as exc:
            return failure(str(exc))

    async def _guarded_flow(
        self, command: LoadOrderCommand, resolved: ResolvedRequest
    ) -> LoadOrderResult:
        blocked = await self._blockers.check(command, resolved)
        if blocked is not None:
            return blocked
        if resolved.is_maintenance_kit:
            return await self._create_incident_and_record(command, resolved)
        try:
            return await self._create_and_record(command, resolved)
        except SerieNoActivaEnCanalDirectoError:
            return await self._handle_inactive_device(command, resolved)
        except InsumoAmbiguoError as exc:
            return self._handle_ambiguous_supply(command, resolved, exc)
        except InsumoNoConfiguradoError as exc:
            return self._handle_insumo_no_configurado(command, resolved, exc)
        except Exception:
            return await self._handle_creation_failed(command, resolved)

    async def _handle_inactive_device(
        self, command: LoadOrderCommand, resolved: ResolvedRequest
    ) -> LoadOrderResult:
        logger.exception(
            "Serie no activa en Canal Directo para request %s", command.hp_request_id
        )
        error = (
            f"El equipo {resolved.device_serial} no está activo en Canal Directo "
            "(posible traslado a bodega/CD1). Verificá su ubicación antes de reintentar."
        )
        await self._record_failure(command, resolved, error)
        return failure(error)

    def _handle_ambiguous_supply(
        self,
        command: LoadOrderCommand,
        resolved: ResolvedRequest,
        exc: InsumoAmbiguoError,
    ) -> LoadOrderResult:
        logger.info(
            "Insumo ambiguo para request %s (serie %s): %d opciones candidatas",
            command.hp_request_id,
            resolved.device_serial,
            len(exc.options),
        )
        return LoadOrderResult(
            ok=False,
            conflict_type=CONFLICT_AMBIGUOUS_INSUMO,
            error="Existen múltiples opciones de insumo para este modelo. "
            "Seleccioná la correcta para continuar.",
            insumo_options=exc.options,
        )

    def _handle_insumo_no_configurado(
        self,
        command: LoadOrderCommand,
        resolved: ResolvedRequest,
        exc: InsumoNoConfiguradoError,
    ) -> LoadOrderResult:
        """A diferencia de _handle_ambiguous_supply, acá ninguna de las opciones de la
        familia es válida (falta cargar el insumo en el catálogo de Canal Directo) — no
        se ofrece selector manual: sin conflict_type ni insumo_options, el frontend cae
        al camino genérico de error en vez de abrir el modal de selección."""
        logger.info(
            "Insumo no configurado en CD para request %s (serie %s): %s",
            command.hp_request_id,
            resolved.device_serial,
            exc,
        )
        return failure(str(exc))

    async def _handle_creation_failed(
        self, command: LoadOrderCommand, resolved: ResolvedRequest
    ) -> LoadOrderResult:
        # Detalle técnico al log del server, no al audit — el historial es visible
        # para cualquier operador (hallazgo #8 del legacy).
        logger.exception("No se pudo crear el pedido para request %s", command.hp_request_id)
        error = (
            "No se pudo crear el pedido en Canal Directo. Verificá la conexión e "
            "intentá de nuevo."
        )
        await self._record_failure(command, resolved, error)
        return failure(error)

    async def _create_and_record(
        self, command: LoadOrderCommand, resolved: ResolvedRequest
    ) -> LoadOrderResult:
        zona = await self._resolve_zone_contacts(command.customer_id, resolved.store_name)
        swap_note = await self._ports.validations.get_swap_note(command.hp_request_id)
        zone_override = detect_sucursal_override(zona.observaciones if zona else None)
        order = build_order_request(command, resolved, zona)
        order_id = await self._create(command, order)
        if not order_id.startswith(_DRYRUN_PREFIX):
            await self._ports.processed.mark_processed(
                build_processed_request(command, resolved, order_id)
            )
            # Pendiente: resolver la alerta activa (request_alerts) al instante.
        await self._ports.audit.record(
            build_audit_created(
                command,
                resolved,
                order_id,
                detail=compose_audit_detail(swap_note, zone_override),
            )
        )
        await self._mark_insight_actioned(command, order_id)
        return success(
            order_id, self._supply_url_for(order_id), resolved.warn, zone_override
        )

    async def _create(self, command: LoadOrderCommand, order: OrderRequest) -> str:
        if command.dry_run:
            order_id = f"{_DRYRUN_PREFIX}{order.reference}"
            logger.info("[DRY RUN] se crearía el pedido %s -> %s", order_id, order)
            return order_id
        return await self._ports.order_creation.create_order(order)

    async def _create_incident_and_record(
        self, command: LoadOrderCommand, resolved: ResolvedRequest
    ) -> LoadOrderResult:
        """Kit de mantenimiento: crea un incidente (tipo Correctivo, ver docstring de
        incident_creation.py) en vez de un pedido — sin resolución de familia/insumo ni
        siembra de supply_cache, y sin marcar Insight actioned (el legacy tampoco lo
        hace para incidentes)."""
        try:
            zona = await self._resolve_zone_contacts(command.customer_id, resolved.store_name)
            zone_override = detect_sucursal_override(zona.observaciones if zona else None)
            incident = build_incident_request(command, resolved, zona)
            incident_id = await self._create_incident(command, incident)
            if not incident_id.startswith(_DRYRUN_PREFIX):
                await self._ports.processed.mark_processed(
                    build_processed_request(command, resolved, incident_id)
                )
            await self._ports.audit.record(
                build_audit_created(
                    command,
                    resolved,
                    incident_id,
                    detail=compose_audit_detail(
                        "Pre-Correctivo (kit de mantenimiento)", zone_override
                    ),
                    order_type=ORDER_TYPE_INCIDENT,
                )
            )
            return success(incident_id, None, resolved.warn, zone_override)
        except Exception:
            return await self._handle_creation_failed(command, resolved)

    async def _create_incident(
        self, command: LoadOrderCommand, incident: IncidentRequest
    ) -> str:
        if command.dry_run:
            incident_id = f"{_DRYRUN_PREFIX}{incident.reference}"
            logger.info("[DRY RUN] se crearía el incidente %s -> %s", incident_id, incident)
            return incident_id
        return await self._ports.incident_creation.create_incident(incident)

    async def _resolve_zone_contacts(self, customer_id: int, zone: str) -> ZoneContacts | None:
        zona = await self._ports.zone_contacts.get(customer_id, zone)
        if zona is None or not zona.has_named_solicitante():
            zona = await self._ports.zone_contacts.get(customer_id, "")
        return zona

    async def _mark_insight_actioned(self, command: LoadOrderCommand, order_id: str) -> None:
        if not self._config.insight_mark_actioned or order_id.startswith(_DRYRUN_PREFIX):
            return
        await update_insight_on_success(self._ports.insight, self._config, command, order_id)

    async def _record_failure(
        self, command: LoadOrderCommand, resolved: ResolvedRequest, detail: str
    ) -> None:
        try:
            await self._ports.audit.record(build_audit_failed(command, resolved, detail))
        except Exception as exc:
            logger.error("No se pudo registrar el evento de auditoría FAILED", exc_info=exc)

    def _supply_url_for(self, order_id: str) -> str | None:
        if order_id.startswith(_DRYRUN_PREFIX):
            return None
        return f"{self._config.order_settings.portal_base_url}/supplies/view/{order_id}"
