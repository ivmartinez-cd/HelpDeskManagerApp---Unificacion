"""Caso de uso LoadOrder — el corazón del módulo (POST /api/requests/{id}/load).

Port del load_request del legacy: re-deriva TODO del lado del servidor contra Insight
(nunca confía en el body), corre los bloqueos 0-3 dentro del claim serie+sku y crea el
pedido con la verificación post-creación obligatoria. Responde siempre con un
LoadOrderResult (el contrato "200 siempre" lo serializa presentation).

Pendiente de pasos posteriores de la migración (explícito, no olvidado):
- Kits de mantenimiento → incidente Pre-Correctivo (falta portar el cliente de
  incidentes, que scrapea el portal): por ahora se responde un error claro.
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
from src.modules.insumos.application.use_cases._load_order_context import (
    LoadOrderConfig,
    LoadOrderPorts,
)
from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    AuditRecord,
)
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.errors import (
    InsumoAmbiguoError,
    OrderAlreadyInProgressError,
    SerieNoActivaEnCanalDirectoError,
)
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.services.maintenance_kit import is_maintenance_kit
from src.modules.insumos.domain.services.stale_replacement import is_stale_replaced
from src.modules.insumos.domain.value_objects.insight_datetime import parse_insight_utc
from src.modules.insumos.domain.value_objects.order_reference import order_reference
from src.modules.insumos.domain.value_objects.order_request import (
    ContactInfo,
    OrderLine,
    OrderRequest,
)
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContacts

logger = logging.getLogger(__name__)

_DRYRUN_PREFIX = "DRYRUN-"


class LoadOrder:
    def __init__(self, ports: LoadOrderPorts, config: LoadOrderConfig) -> None:
        self._ports = ports
        self._config = config
        self._blockers = LoadOrderBlockers(ports, config)

    async def execute(self, command: LoadOrderCommand) -> LoadOrderResult:
        resolved = await self._resolve_request(command)
        if isinstance(resolved, LoadOrderResult):
            return resolved

        async def guarded() -> LoadOrderResult:
            return await self._guarded_flow(command, resolved)

        try:
            return await self._ports.claimed_creation.run(
                device_serial=resolved.device_serial, sku=resolved.sku, action=guarded
            )
        except OrderAlreadyInProgressError as exc:
            # El legacy esperaba en el KeyedLock; con el claim de Postgres el segundo
            # intento concurrente recibe un error de negocio inmediato en su lugar.
            return failure(str(exc))

    # ------------------------------------------------- resolver contra Insight --

    async def _resolve_request(
        self, command: LoadOrderCommand
    ) -> ResolvedRequest | LoadOrderResult:
        """Nunca confiar en el body: deviceId/serial/sku se derivan releyendo Insight."""
        try:
            requests = await self._ports.insight.get_consumable_requests(
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
        return await self._resolve_device(command, matched)

    async def _resolve_device(
        self, command: LoadOrderCommand, matched: JsonDict
    ) -> ResolvedRequest | LoadOrderResult:
        device_id = int(matched["deviceId"])
        device = await self._ports.insight.get_device_by_id(device_id)
        device_serial = str(device.get("serialNumber") or "")
        if not device_serial:
            logger.warning(
                "load_order: request %s (deviceId=%s) sin número de serie en Insight",
                command.hp_request_id,
                device_id,
            )
            return failure("No se pudo determinar el número de serie del equipo desde Insight.")

        consumable = matched.get("consumable") or {}
        percent_left = consumable.get("percentLeft")
        days_left = consumable.get("daysLeft")
        warn = None
        if percent_left is None or days_left is None:
            warn = (
                "No se pudo obtener el nivel de consumible; el pedido se creó sin esa información."
            )
        reorder_part = consumable.get("reorderPart") or {}
        return ResolvedRequest(
            hp_request_id=command.hp_request_id,
            device_id=device_id,
            device_serial=device_serial,
            store_name=str((device.get("extendedFields") or {}).get("zone") or ""),
            sku=str(consumable.get("sku") or ""),
            description=str(consumable.get("description") or ""),
            percent_left=percent_left,
            days_left=days_left,
            pages_left=consumable.get("pagesLeft"),
            requested=matched.get("requested"),
            is_maintenance_kit=is_maintenance_kit(
                str(consumable.get("description") or ""), str(reorder_part.get("type") or "")
            ),
            warn=warn,
        )

    # ------------------------------------------------------- flujo con claim --

    async def _guarded_flow(
        self, command: LoadOrderCommand, resolved: ResolvedRequest
    ) -> LoadOrderResult:
        blocked = await self._blockers.check(command, resolved)
        if blocked is not None:
            return blocked
        if resolved.is_maintenance_kit:
            return failure(
                "Esta solicitud es un kit de mantenimiento: va como incidente "
                "Pre-Correctivo, que todavía no está portado al monolito. Cargala desde "
                "la app legacy de SDSInsumos."
            )
        try:
            return await self._create_and_record(command, resolved)
        except SerieNoActivaEnCanalDirectoError:
            logger.exception(
                "Serie no activa en Canal Directo para request %s", command.hp_request_id
            )
            error = (
                f"El equipo {resolved.device_serial} no está activo en Canal Directo "
                "(posible traslado a bodega/CD1). Verificá su ubicación antes de reintentar."
            )
            await self._record_failure(command, resolved, error)
            return failure(error)
        except InsumoAmbiguoError as exc:
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
        except Exception:
            # El detalle técnico completo va al log del server, no al audit (el
            # historial es visible para cualquier operador — hallazgo #8 del legacy).
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
        order = _build_order_request(command, resolved, zona)

        order_id = await self._create(command, order)
        if not order_id.startswith(_DRYRUN_PREFIX):
            await self._ports.processed.mark_processed(_processed_from(command, resolved, order_id))
            # Pendiente: resolver la alerta activa (request_alerts) al instante — llega
            # con el port del módulo de alertas.
        await self._ports.audit.record(
            _audit_created(command, resolved, order_id, detail=swap_note or None)
        )
        await self._mark_insight_actioned(command, order_id)
        return success(order_id, self._supply_url_for(order_id), resolved.warn)

    async def _create(self, command: LoadOrderCommand, order: OrderRequest) -> str:
        if command.dry_run:
            order_id = f"{_DRYRUN_PREFIX}{order.reference}"
            logger.info("[DRY RUN] se crearía el pedido %s -> %s", order_id, order)
            return order_id
        return await self._ports.order_creation.create_order(order)

    async def _resolve_zone_contacts(self, customer_id: int, zone: str) -> ZoneContacts | None:
        """Zona exacta → zona default "" (un registro sin nombre/apellido es inútil)."""
        zona = await self._ports.zone_contacts.get(customer_id, zone)
        if zona is None or not zona.has_named_solicitante():
            zona = await self._ports.zone_contacts.get(customer_id, "")
        return zona

    async def _mark_insight_actioned(self, command: LoadOrderCommand, order_id: str) -> None:
        if not self._config.insight_mark_actioned or order_id.startswith(_DRYRUN_PREFIX):
            return
        try:
            await self._ports.insight.update_consumable_request(
                request_id=command.hp_request_id,
                external_ref=f"CD-{order_id}",
                status_update=self._config.insight_status_on_order,
                comment=f"Pedido creado en Canal Directo: {order_id}",
            )
            logger.info(
                "Insight request %s marcada como %s (ref CD-%s)",
                command.hp_request_id,
                self._config.insight_status_on_order,
                order_id,
            )
        except Exception as exc:
            logger.error(
                "No se pudo actualizar Insight para request %s (pedido %s ya creado en CD)",
                command.hp_request_id,
                order_id,
                exc_info=exc,
            )

    async def _record_failure(
        self, command: LoadOrderCommand, resolved: ResolvedRequest, detail: str
    ) -> None:
        try:
            await self._ports.audit.record(
                AuditRecord(
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
            )
        except Exception as exc:
            logger.error("No se pudo registrar el evento de auditoría FAILED", exc_info=exc)

    def _supply_url_for(self, order_id: str) -> str | None:
        if order_id.startswith(_DRYRUN_PREFIX):
            return None
        return f"{self._config.order_settings.portal_base_url}/supplies/view/{order_id}"


def _build_order_request(
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
        detalle=_build_detalle(resolved, zona.observaciones if zona else ""),
        override_insumo_id=command.override_insumo_id,
        revision=command.revision,
    )


def _order_contacts(zona: ZoneContacts | None) -> tuple[ContactInfo | None, ContactInfo | None]:
    """Solo se usa el contacto per-zona si tiene al menos nombre o apellido — si no,
    la resolución en 3 capas de la creación cae al prefill/config global."""
    if zona is None:
        return None, None
    sol = zona.solicitante
    dest = zona.destinatario
    solicitante = sol if (sol.apellido.strip() or sol.nombre.strip()) else None
    destinatario = dest if (dest.apellido.strip() or dest.nombre.strip()) else None
    return solicitante, destinatario


def _build_detalle(resolved: ResolvedRequest, observaciones: str) -> str:
    parts = []
    if resolved.percent_left is not None:
        value = float(resolved.percent_left)
        parts.append(f"le queda {int(value) if value.is_integer() else value}%")
    if resolved.pages_left is not None:
        parts.append(f"({resolved.pages_left} pág. rest.)")
    if resolved.days_left is not None:
        parts.append(f"para consumirse en {resolved.days_left} días")
    detalle = " ".join(parts)
    # La nota de zona va primero: quien arma el envío la ve antes que el texto
    # autogenerado del consumible.
    if observaciones.strip():
        detalle = f"{observaciones.strip()} {detalle}".strip()
    return detalle


def _processed_from(
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
        initial_percent_left=_rounded(resolved.percent_left),
        initial_days_left=resolved.days_left,
        initial_pages_left=resolved.pages_left,
    )


def _audit_created(
    command: LoadOrderCommand, resolved: ResolvedRequest, order_id: str, detail: str | None
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
        initial_percent_left=_rounded(resolved.percent_left),
        initial_days_left=resolved.days_left,
        initial_pages_left=resolved.pages_left,
    )


def _rounded(value: float | None) -> int | None:
    return round(value) if value is not None else None
