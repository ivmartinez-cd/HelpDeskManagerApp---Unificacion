"""Fase de asociación de ListRequests: vincular cada fila con su pedido real en CD.

Port del bloque central de list_requests (routers/requests/query.py):
1. Cache hits (supply activo por serie) + órdenes propias.
2. Refresh SOAP deduplicado del estado de pedidos propios y activos (kit-aware),
   persistiendo al cache y releyéndolo; fallback al estado cacheado si el SOAP falló.
3. Lookup del portal para series sin hit de cache.
4. Por fila: liberar el pedido propio si quedó Anulado/Cancelado en CD (audit RELEASED,
   la fila vuelve a "Sin cargar"), o asociar por cache/portal/fecha, o mostrar el estado
   del pedido propio (incidente para kits, "Creado (Simulado)" para dry-run).
"""

import logging
from dataclasses import dataclass, field

from src.modules.insumos.application.dtos.request_rows import RequestRow
from src.modules.insumos.application.use_cases.get_dashboard import GetDashboardPorts
from src.modules.insumos.domain.entities.audit_record import EVENT_RELEASED, AuditRecord
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.services.supply_lookup import CanalDirectoSupplyLookup
from src.modules.insumos.domain.services.supply_request_matching import (
    SupplyMatchQuery,
    match_active_supply,
    match_supply_for_request,
    supply_matches_request,
)
from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_supply import (
    ActiveSupplyView,
    CachedSupply,
    CdSupply,
)
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.domain.value_objects.serial_number import serial_from_supply_fields
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

logger = logging.getLogger(__name__)

_DRYRUN_PREFIX = "DRYRUN-"


@dataclass(frozen=True)
class AssociationContext:
    dashboard: GetDashboardPorts
    supply_lookup: CanalDirectoSupplyLookup
    order_settings: CanalDirectoOrderSettings


@dataclass
class _State:
    cache_hits: dict[str, CachedSupply] = field(default_factory=dict)
    supplies_by_serial: dict[str, list[CachedSupply]] = field(default_factory=dict)
    own_orders: dict[str, list[ProcessedRequest]] = field(default_factory=dict)
    live_states: dict[int, str] = field(default_factory=dict)
    portal: dict[str, list[ActiveSupplyView]] = field(default_factory=dict)


class RequestAssociation:
    def __init__(self, context: AssociationContext) -> None:
        self._ctx = context

    async def associate(self, rows: list[RequestRow]) -> None:
        state = _State()
        serials = sorted({r.serial for r in rows if r.serial})
        await self._load_cache(state, serials)
        await self._refresh_live_states(state, rows, serials)
        await self._load_portal(state, serials)
        for row in rows:
            await self._associate_row(state, row)

    async def _load_cache(self, state: _State, serials: list[str]) -> None:
        state.supplies_by_serial = (
            await self._ctx.dashboard.supply_cache.get_noncancelled_by_serials(serials)
        )
        state.cache_hits = {
            key: active
            for key, supplies in state.supplies_by_serial.items()
            if (active := match_active_supply(supplies)) is not None
        }
        state.own_orders = await self._ctx.dashboard.processed.get_created_by_serials(serials)

    async def _refresh_live_states(
        self, state: _State, rows: list[RequestRow], serials: list[str]
    ) -> None:
        to_check = _orders_to_check(state, rows)
        if not to_check:
            return
        results = [
            (sid, await self._fetch_live(sid, is_kit)) for sid, (is_kit, serial) in to_check.items()
        ]
        cache_updates = []
        for sid, item in results:
            if item is None:
                continue
            state.live_states[sid] = item.estado
            if not to_check[sid][0]:  # los incidentes no van al cache de supplies
                cache_updates.append(_cache_entry(sid, item, to_check[sid][1]))
        if cache_updates:
            await self._ctx.dashboard.supply_cache.upsert(cache_updates)
            await self._load_cache(state, serials)  # releer hits frescos
        missing = [sid for sid in to_check if sid not in state.live_states]
        if missing:
            cached = await self._ctx.dashboard.supply_cache.get_statuses_batch(missing)
            state.live_states.update({sid: estado for sid, estado in cached.items() if estado})

    async def _fetch_live(self, supply_id: int, is_kit: bool) -> CdSupply | None:
        if is_kit:
            return await self._ctx.dashboard.wsayc.fetch_incident_by_id(supply_id)
        return await self._ctx.dashboard.wsayc.fetch_supply_by_id(supply_id)

    async def _load_portal(self, state: _State, serials: list[str]) -> None:
        """Series sin hit de cache: mirar los pedidos activos visibles en el portal."""
        to_portal = [s for s in serials if s.upper() not in state.cache_hits]
        for serial in to_portal:
            try:
                state.portal[serial] = await self._ctx.supply_lookup.lookup_supplies_by_serial(
                    serial
                )
            except Exception as exc:
                logger.error(
                    "list_requests: lookup del portal falló para serie %s", serial, exc_info=exc
                )

    # ------------------------------------------------------------------ por fila --

    async def _associate_row(self, state: _State, row: RequestRow) -> None:
        if await self._release_if_cancelled(state, row):
            return
        if self._associate_from_cache(state, row):
            return
        if self._associate_from_portal(state, row):
            return
        self._associate_by_date(state, row)
        if not row.supply_id and row.order_id:
            self._show_own_order_status(state, row)

    async def _release_if_cancelled(self, state: _State, row: RequestRow) -> bool:
        """El pedido propio quedó Anulado/Cancelado en CD: mostrar ese estado, limpiar
        orderId (la fila vuelve a "Sin cargar") y liberar el registro local."""
        order_id = row.order_id
        if not order_id or order_id.startswith(_DRYRUN_PREFIX):
            return False
        supply_id = _numeric_id(order_id)
        if supply_id is None:
            return False
        estado = state.live_states.get(supply_id)
        if estado not in cd_state.RELEASE_STATES:
            return False
        row.order_id = None
        row.supply_id = order_id
        row.supply_url = self._ctx.order_settings.supply_web_url(supply_id)
        row.supply_status = estado
        logger.info(
            "list_requests: supply %d %s → liberando solicitud %d",
            supply_id,
            estado,
            row.request_id,
        )
        processed = await self._ctx.dashboard.processed.get(row.request_id)
        await self._ctx.dashboard.processed.mark_cancelled(row.request_id)
        await self._ctx.dashboard.audit.record(
            _released_record(row, order_id, f"supply {supply_id} {estado}", processed)
        )
        return True

    def _associate_from_cache(self, state: _State, row: RequestRow) -> bool:
        hit = state.cache_hits.get(row.serial.upper()) if row.serial else None
        if hit is None or not supply_matches_request(
            hit, self._query_for(state, row), for_ui_display=True
        ):
            return False
        row.supply_id = supply_id_full(hit.supply_id)
        row.supply_url = self._ctx.order_settings.supply_web_url(hit.supply_id)
        row.supply_status = hit.estado
        return True

    def _associate_from_portal(self, state: _State, row: RequestRow) -> bool:
        for view in state.portal.get(row.serial, []):
            if view.estado in (cd_state.ANULADO, cd_state.CANCELADO):
                continue
            candidate = _portal_candidate(view, row.serial)
            if candidate is not None and supply_matches_request(
                candidate, self._query_for(state, row), for_ui_display=True
            ):
                row.supply_id = view.nro
                row.supply_url = view.url
                row.supply_status = view.estado
                return True
        return False

    def _associate_by_date(self, state: _State, row: RequestRow) -> None:
        """Supply creado en o después de la fecha de la solicitud: se adopta también
        como orderId (la fila pasa a "cargada"), igual que el legacy."""
        if not row.serial or row.requested_day is None:
            return
        supplies = state.supplies_by_serial.get(row.serial.upper(), [])
        match = match_supply_for_request(supplies, row.requested_day)
        if match is None or not supply_matches_request(
            match, self._query_for(state, row), for_ui_display=True
        ):
            return
        nro = supply_id_full(match.supply_id)
        row.supply_id = nro
        row.supply_url = self._ctx.order_settings.supply_web_url(match.supply_id)
        row.supply_status = match.estado
        row.order_id = nro

    def _show_own_order_status(self, state: _State, row: RequestRow) -> None:
        order_id = row.order_id
        assert order_id is not None
        if order_id.startswith(_DRYRUN_PREFIX):
            row.supply_id = order_id
            row.supply_status = "Creado (Simulado)"
            return
        supply_id = _numeric_id(order_id)
        if supply_id is None:
            return
        row.supply_id = order_id
        row.supply_status = state.live_states.get(supply_id)
        if row.is_maintenance_kit:
            base = self._ctx.order_settings.portal_base_url
            row.supply_url = f"{base}/incidents/view/{order_id}"
        else:
            row.supply_url = self._ctx.order_settings.supply_web_url(supply_id)

    def _query_for(self, state: _State, row: RequestRow) -> SupplyMatchQuery:
        own = state.own_orders.get(row.serial.upper(), []) if row.serial else []
        return SupplyMatchQuery(sku=row.sku, description=row.description, own_orders=tuple(own))


def _orders_to_check(state: _State, rows: list[RequestRow]) -> dict[int, tuple[bool, str]]:
    """{supply_id: (es_kit, serial)} deduplicado: pedidos propios + activos del cache."""
    to_check: dict[int, tuple[bool, str]] = {}
    for row in rows:
        if row.order_id and not row.order_id.startswith(_DRYRUN_PREFIX):
            supply_id = _numeric_id(row.order_id)
            if supply_id is not None and supply_id not in to_check:
                to_check[supply_id] = (row.is_maintenance_kit, row.serial)
        hit = state.cache_hits.get(row.serial.upper()) if row.serial else None
        if hit is not None and hit.supply_id not in to_check:
            to_check[hit.supply_id] = (row.is_maintenance_kit, row.serial)
    return to_check


def _numeric_id(order_id: str) -> int | None:
    try:
        return int(order_id.split("-")[0])
    except (ValueError, IndexError):
        return None


def _cache_entry(supply_id: int, item: CdSupply, serial: str) -> CachedSupply:
    return CachedSupply(
        supply_id=supply_id,
        serial=serial or serial_from_supply_fields(item.nro_serie_solicitud, item.nro_serie),
        estado=item.estado,
        empresa_id=item.empresa_id,
        fecha=parse_cd_datetime(item.fecha),
    )


def _portal_candidate(view: ActiveSupplyView, serial: str) -> CachedSupply | None:
    """Adapta la vista del portal al candidato del matching (el portal no trae SKU ni
    descripción — el matching cae en las reglas de 'sin datos')."""
    supply_id = _numeric_id(view.nro)
    if supply_id is None:
        return None
    return CachedSupply(supply_id=supply_id, serial=serial, estado=view.estado)


def _released_record(
    row: RequestRow, order_id: str, detail: str, processed: ProcessedRequest | None
) -> AuditRecord:
    return AuditRecord(
        event=EVENT_RELEASED,
        hp_request_id=row.request_id,
        customer_id=row.customer_id,
        customer_name=row.customer_name,
        device_serial=row.serial or (processed.device_serial if processed else None),
        sku=row.sku or (processed.sku if processed else None),
        internal_order_id=order_id,
        detail=detail,
        description=row.description or (processed.description if processed else None),
    )
