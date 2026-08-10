"""Bloqueos previos a crear el pedido (bloqueos 0-3 del legacy load_request), en orden.

Corren SIEMPRE dentro del claim serie+sku (ClaimedOrderCreation) — correrlos afuera
reabriría la carrera check-then-act que el claim cierra. De los cuatro, solo el tope
diario NO tiene bypass con forceOverride.
"""

import logging
from datetime import UTC
from zoneinfo import ZoneInfo

from src.modules.insumos.application.dtos.load_order import (
    CONFLICT_ACTIVE_SUPPLY,
    CONFLICT_PENDING_VALIDATION,
    CONFLICT_TODAY_ORDER,
    LoadOrderCommand,
    LoadOrderResult,
    ResolvedRequest,
    conflict,
    failure,
    success,
)
from src.modules.insumos.application.use_cases._load_order_context import (
    LoadOrderConfig,
    LoadOrderPorts,
)
from src.modules.insumos.domain.entities.processed_request import STATUS_CANCELLED
from src.modules.insumos.domain.services.supply_request_matching import SupplyMatchQuery
from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_datetime import format_cd_datetime
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

logger = logging.getLogger(__name__)

# Tope duro (sin forceOverride) de cargas reales por solicitud por día. Un ciclo normal
# cancelar+recargar (corregir un SKU) nunca lo toca — frena un loop scripteado, que no
# deja rastro en processed_requests porque cancelar borra el registro ahí (no en audit).
CANCEL_RELOAD_DAILY_LIMIT = 3

_DRYRUN_PREFIX = "DRYRUN-"


class LoadOrderBlockers:
    def __init__(self, ports: LoadOrderPorts, config: LoadOrderConfig) -> None:
        self._ports = ports
        self._config = config

    async def check(
        self, command: LoadOrderCommand, request: ResolvedRequest
    ) -> LoadOrderResult | None:
        """None = ningún bloqueo aplica; un LoadOrderResult corta el flujo (puede ser
        ok=True: el caso "ya procesado" responde idempotente sin crear nada)."""
        for blocker in (
            self._pending_validation,
            self._already_processed,
            self._today_order,
            self._active_supply,
            self._daily_cap,
        ):
            result = await blocker(command, request)
            if result is not None:
                return result
        return None

    async def _pending_validation(
        self, command: LoadOrderCommand, request: ResolvedRequest
    ) -> LoadOrderResult | None:
        """Bloqueo 0: la solicitud llegó directo a un nivel muy bajo sin descenso gradual
        previo — puede ser falla de lectura del sensor. Saltable con forceOverride."""
        if command.force_override:
            return None
        pending = await self._ports.validations.get_pending(command.hp_request_id)
        if pending is None:
            return None
        deadline_utc = pending.deadline_at.astimezone(UTC)
        return conflict(
            CONFLICT_PENDING_VALIDATION,
            "Esta solicitud llegó directo a un nivel muy bajo, sin bajada gradual previa "
            "— puede ser una falla de lectura del sensor. Se vuelve a confirmar "
            "automáticamente contra Insight antes de habilitar la carga.",
            {
                "deadlineAt": deadline_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "initialPercentLeft": pending.initial_percent_left,
                "diagnosisHeadline": pending.diagnosis_headline,
                "diagnosisDetail": pending.diagnosis_detail,
            },
        )

    async def _already_processed(
        self, command: LoadOrderCommand, request: ResolvedRequest
    ) -> LoadOrderResult | None:
        """Respuesta idempotente si el pedido sigue vigente; si en CD ya figura
        Anulado/Cancelado, se limpia el registro stale y se permite crear uno nuevo."""
        existing = await self._ports.processed.get(command.hp_request_id)
        if existing is None or existing.status == STATUS_CANCELLED:
            return None
        order_id = existing.internal_order_id
        if not order_id.startswith(_DRYRUN_PREFIX) and await self._released_in_cd(order_id):
            logger.info(
                "Pedido %s anulado/cancelado en CD; registro stale eliminado para request %s",
                order_id,
                command.hp_request_id,
            )
            await self._ports.processed.mark_cancelled(command.hp_request_id)
            return None
        return success(order_id, self._supply_url_for(order_id))

    async def _released_in_cd(self, order_id: str) -> bool:
        try:
            supply_id = int(order_id.split("-")[0])
        except (ValueError, IndexError):
            return False
        status = await self._ports.supply_cache.get_status(supply_id)
        return status in cd_state.RELEASE_STATES

    async def _today_order(
        self, command: LoadOrderCommand, request: ResolvedRequest
    ) -> LoadOrderResult | None:
        """Bloqueo 1: ya se cargó un pedido HOY (día argentino) para esta serie+sku."""
        if command.force_override:
            return None
        today = await self._ports.processed.get_today_order_for(
            request.device_serial, request.sku
        )
        if today is None:
            return None
        created_at = ""
        if today.created_at is not None:
            created_at = today.created_at.astimezone(ZoneInfo(self._config.timezone)).strftime(
                "%d/%m/%Y %H:%M"
            )
        return conflict(
            CONFLICT_TODAY_ORDER,
            f"Ya se cargó un pedido para esta serie ({request.device_serial}) y "
            "consumible hoy.",
            {
                "deviceSerial": today.device_serial,
                "sku": today.sku,
                "orderId": today.internal_order_id,
                "createdAt": created_at,
                "supplyUrl": self._supply_url_for(today.internal_order_id),
            },
        )

    async def _active_supply(
        self, command: LoadOrderCommand, request: ResolvedRequest
    ) -> LoadOrderResult | None:
        """Bloqueo 2: hay un pedido activo en CD para la serie — con resolve por
        SKU/color para no bloquear por el pedido de OTRO consumible (bug 441448)."""
        if command.dry_run or command.force_override:
            return None
        cached = await self._ports.supply_cache.find_active_by_serial(request.device_serial)
        if cached is None:
            return None
        own_orders = await self._ports.processed.get_created_by_serial(request.device_serial)
        query = SupplyMatchQuery(
            sku=request.sku, description=request.description, own_orders=tuple(own_orders)
        )
        if not await self._ports.match_resolver.resolve(cached, query, for_ui_display=False):
            return None
        nro = supply_id_full(cached.supply_id)
        return conflict(
            CONFLICT_ACTIVE_SUPPLY,
            f"Ya existe un pedido activo ({nro}, estado: {cached.estado}) para la serie "
            f"{request.device_serial} en Canal Directo.",
            {
                "deviceSerial": cached.serial,
                "supplyId": nro,
                "estado": cached.estado,
                "fecha": format_cd_datetime(cached.fecha) or None,
                "supplyUrl": self._config.order_settings.supply_web_url(cached.supply_id),
            },
        )

    async def _daily_cap(
        self, command: LoadOrderCommand, request: ResolvedRequest
    ) -> LoadOrderResult | None:
        """Bloqueo 3: tope de cargas reales por día para esta solicitud — NUNCA se
        saltea, ni con forceOverride (techo anti-abuso real)."""
        if command.dry_run:
            return None
        created_today = await self._ports.audit.count_created_today(command.hp_request_id)
        if created_today < CANCEL_RELOAD_DAILY_LIMIT:
            return None
        return failure(
            f"Esta solicitud ya se cargó {created_today} veces hoy (máximo "
            f"{CANCEL_RELOAD_DAILY_LIMIT} por día). Si necesitás cargarla de nuevo, "
            "contactá a soporte."
        )

    def _supply_url_for(self, order_id: str) -> str | None:
        if not order_id or order_id.startswith(_DRYRUN_PREFIX):
            return None
        return f"{self._config.order_settings.portal_base_url}/supplies/view/{order_id}"
