"""Matching entre un supply existente en Canal Directo y una solicitud de Insight.

Port de supply_matches_request / extract_color_from_text (db/supplies.py) y
resolve_supply_match (poller.py). Previene atribuirle a una alerta (ej. Toner Negro)
el pedido de OTRO consumible (ej. Toner Cyan 441448-7 — bug real 971496).
"""

import re
from dataclasses import dataclass, replace

from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply

_COLOR_KEYWORDS = {
    "black": ("black", "negro"),
    "cyan": ("cyan", "cian", "celeste"),
    "magenta": ("magenta",),
    "yellow": ("yellow", "amarillo"),
}

# Convenciones de SKU Samsung/HP: CLT-K404S, K404, "-K" suelto, etc.
_SKU_COLOR_PATTERNS = (
    ("black", (r"\bclt-k\d", r"\bk\d{3}[a-z]?\b", r"[-_\s]k[0-9-\s$]")),
    ("cyan", (r"\bclt-c\d", r"\bc\d{3}[a-z]?\b", r"[-_\s]c[0-9-\s$]")),
    ("magenta", (r"\bclt-m\d", r"\bm\d{3}[a-z]?\b", r"[-_\s]m[0-9-\s$]")),
    ("yellow", (r"\bclt-y\d", r"\by\d{3}[a-z]?\b", r"[-_\s]y[0-9-\s$]")),
)


def extract_color_from_text(text: str | None) -> str | None:
    """Extrae el color de un consumible desde su SKU o descripción."""
    if not text:
        return None
    lowered = str(text).lower()
    for color, keywords in _COLOR_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return color
    for color, patterns in _SKU_COLOR_PATTERNS:
        if any(re.search(p, lowered) for p in patterns):
            return color
    return None


@dataclass(frozen=True)
class SupplyMatchQuery:
    """La solicitud contra la que se compara el supply, más las órdenes propias de la
    serie (processed_requests) — la única fuente que conoce el consumible real de un
    pedido creado por esta app."""

    sku: str
    description: str = ""
    own_orders: tuple[ProcessedRequest, ...] = ()


def supply_matches_request(
    candidate: CachedSupply, query: SupplyMatchQuery, for_ui_display: bool = True
) -> bool:
    """¿El supply existente corresponde a esta solicitud?

    `for_ui_display=True` (dashboard): solo True con match confirmado o muy probable.
    `for_ui_display=False` (poller / bloqueos de /load): ante duda total sin SKU ni
    descripción se asume True por prudencia anti-duplicado — preferible bloquear una
    carga legítima a duplicar un pedido (mismo patrón que el caso CN4766M07W, 2026-08-05).
    """
    req_sku = query.sku.strip().upper()
    req_desc = query.description.strip()

    own_verdict = _match_against_own_order(candidate, req_sku, req_desc, query.own_orders)
    if own_verdict is not None:
        return own_verdict
    sku_verdict = _match_by_supply_sku(candidate, req_sku, req_desc)
    if sku_verdict is not None:
        return sku_verdict
    color_verdict = _match_by_description_color(candidate, req_sku, req_desc)
    if color_verdict is not None:
        return color_verdict

    sup_sku = candidate.sku.strip().upper()
    if for_ui_display and sup_sku and req_sku and sup_sku != req_sku:
        return False
    return not for_ui_display


def _match_against_own_order(
    candidate: CachedSupply,
    req_sku: str,
    req_desc: str,
    own_orders: tuple[ProcessedRequest, ...],
) -> bool | None:
    """Si el supply es un pedido creado por esta app, su SKU registrado es la verdad."""
    own = next((o for o in own_orders if _own_order_supply_id(o) == candidate.supply_id), None)
    if own is None:
        return None
    own_sku = own.sku.strip().upper()
    if own_sku:
        return own_sku == req_sku or own_sku in req_sku or req_sku in own_sku
    own_desc = own.description.strip()
    if own_desc:
        own_color = extract_color_from_text(own_desc)
        req_color = extract_color_from_text(req_desc or req_sku)
        if own_color and req_color and own_color != req_color:
            return False
    return None


def _own_order_supply_id(order: ProcessedRequest) -> int | None:
    try:
        return int(order.internal_order_id.split("-")[0])
    except (ValueError, IndexError):
        return None


def _match_by_supply_sku(candidate: CachedSupply, req_sku: str, req_desc: str) -> bool | None:
    sup_sku = candidate.sku.strip().upper()
    if not (sup_sku and req_sku):
        return None
    if sup_sku == req_sku or sup_sku in req_sku or req_sku in sup_sku:
        return True
    sup_color = extract_color_from_text(sup_sku)
    req_color = extract_color_from_text(req_sku or req_desc)
    if sup_color and req_color and sup_color != req_color:
        return False
    # SKUs distintos con señal de color en al menos uno y colores no coincidentes:
    # también descarta (port literal del legacy, incluida la asimetría del criterio).
    skus_comparables = len(sup_sku) >= 3 and len(req_sku) >= 3 and sup_sku != req_sku
    if skus_comparables and (sup_color or req_color) and sup_color != req_color:
        return False
    return None


def _match_by_description_color(
    candidate: CachedSupply, req_sku: str, req_desc: str
) -> bool | None:
    sup_desc = candidate.description.strip()
    sup_color = extract_color_from_text(sup_desc or candidate.sku.strip().upper())
    req_color = extract_color_from_text(req_desc or req_sku)
    if sup_color and req_color:
        return sup_color == req_color
    return None


class SupplyMatchResolver:
    """Como supply_matches_request, pero completa la descripción faltante vía SOAP antes
    de resolver por descarte de datos vacíos (port de poller.resolve_supply_match).

    El SOAP no trae NroArticulo/Descripcion: solo conocemos el consumible real de un
    supply si esta app lo creó (own_orders) o consultando sus detalles. Sin este paso,
    todo pedido de origen externo caería en el fallback "sin datos → asumir match" —
    exactamente el bug 441448/971496. Llamar SOLO en paths de bloqueo/creación, no en
    vistas de solo lectura (que se benefician del cache una vez completado).
    """

    def __init__(self, gateway: WsAycGateway, cache: SupplyCacheRepository) -> None:
        self._gateway = gateway
        self._cache = cache

    async def resolve(
        self, candidate: CachedSupply, query: SupplyMatchQuery, for_ui_display: bool
    ) -> bool:
        if supply_matches_request(candidate, query, for_ui_display) is False:
            return False
        if candidate.sku.strip() or candidate.description.strip():
            return True

        description = await self._gateway.get_supply_description(candidate.supply_id)
        if not description:
            return True

        enriched = replace(candidate, sku="", description=description)
        await self._cache.upsert([enriched])
        return supply_matches_request(enriched, query, for_ui_display)
