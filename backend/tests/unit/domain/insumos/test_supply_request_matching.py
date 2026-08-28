"""Tests de caracterización del matching supply↔solicitud (bugs reales 441448/971496
y CN4766M07W documentados en la caracterización)."""

from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.services.supply_request_matching import (
    SupplyMatchQuery,
    SupplyMatchResolver,
    extract_color_from_text,
    supply_matches_request,
)
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply
from tests.unit.domain.insumos.fakes import FakeSupplyCacheRepository, FakeWsAycGateway


def _candidate(**overrides: object) -> CachedSupply:
    base: dict[str, object] = {"supply_id": 441448, "serial": "SERIE1", "estado": "Pendiente"}
    base.update(overrides)
    return CachedSupply(**base)  # type: ignore[arg-type]


def _own(internal_order_id: str, sku: str = "", description: str = "") -> ProcessedRequest:
    return ProcessedRequest(
        hp_request_id=1, internal_order_id=internal_order_id, sku=sku, description=description
    )


# --- extract_color_from_text -----------------------------------------------------------


def test_extract_color_por_palabra_en_espanol_o_ingles() -> None:
    assert extract_color_from_text("Cartucho amarillo HP 414A") == "yellow"
    assert extract_color_from_text("Black Toner") == "black"
    assert extract_color_from_text("Toner cian") == "cyan"
    assert extract_color_from_text("sin color") is None
    assert extract_color_from_text(None) is None


def test_extract_color_por_convencion_de_sku_samsung() -> None:
    assert extract_color_from_text("CLT-K404S") == "black"
    assert extract_color_from_text("CLT-C404S") == "cyan"


# --- supply_matches_request ------------------------------------------------------------


def test_pedido_propio_con_mismo_sku_matchea() -> None:
    query = SupplyMatchQuery(sku="CF230A", own_orders=(_own("441448-7", sku="CF230A"),))
    assert supply_matches_request(_candidate(), query, for_ui_display=False)


def test_pedido_propio_con_otro_sku_no_matchea() -> None:
    """Bug real 441448/971496: el pedido de OTRO consumible de la misma serie no debe
    bloquear la carga del correcto."""
    query = SupplyMatchQuery(sku="W9008MC", own_orders=(_own("441448-7", sku="CF230A"),))
    assert not supply_matches_request(_candidate(), query, for_ui_display=False)


def test_colores_distintos_por_descripcion_no_matchea() -> None:
    query = SupplyMatchQuery(sku="", description="Toner negro HP")
    candidate = _candidate(description="Toner Cyan HP")
    assert not supply_matches_request(candidate, query, for_ui_display=False)


def test_mismo_color_matchea() -> None:
    query = SupplyMatchQuery(sku="", description="Cartucho amarillo")
    candidate = _candidate(description="Yellow Toner")
    assert supply_matches_request(candidate, query, for_ui_display=False)


def test_sku_del_supply_por_substring_matchea() -> None:
    query = SupplyMatchQuery(sku="CF230A")
    assert supply_matches_request(_candidate(sku="CF230"), query, for_ui_display=False)


def test_sin_datos_bloquea_en_paths_de_creacion_pero_no_en_ui() -> None:
    """Caso real CN4766M07W (2026-08-05): sin SKU ni color utilizable, el poller/load
    asume match por prudencia anti-duplicado; la UI NO da la solicitud por cubierta."""
    query = SupplyMatchQuery(sku="CF230A")
    candidate = _candidate()  # sin sku ni descripción
    assert supply_matches_request(candidate, query, for_ui_display=False)
    assert not supply_matches_request(candidate, query, for_ui_display=True)


# --- SupplyMatchResolver ---------------------------------------------------------------


async def test_resolver_completa_descripcion_y_descarta_otro_color() -> None:
    """Sin el fetch de descripción, todo pedido externo caería en "sin datos → match";
    con la descripción real de otro color, el bloqueo se levanta correctamente."""
    gateway = FakeWsAycGateway()
    gateway.description = "Toner Cyan Samsung"
    cache = FakeSupplyCacheRepository()
    resolver = SupplyMatchResolver(gateway, cache)

    query = SupplyMatchQuery(sku="", description="Toner negro Samsung")
    result = await resolver.resolve(_candidate(), query, for_ui_display=False)

    assert result is False
    # La descripción obtenida queda persistida para no repetir el fetch.
    assert cache.entries[0].description == "Toner Cyan Samsung"


async def test_resolver_sin_descripcion_disponible_asume_match_por_prudencia() -> None:
    gateway = FakeWsAycGateway()
    gateway.description = ""
    resolver = SupplyMatchResolver(gateway, FakeSupplyCacheRepository())

    query = SupplyMatchQuery(sku="CF230A")
    assert await resolver.resolve(_candidate(), query, for_ui_display=False) is True


async def test_resolver_con_datos_presentes_no_toca_la_red() -> None:
    gateway = FakeWsAycGateway()
    resolver = SupplyMatchResolver(gateway, FakeSupplyCacheRepository())

    query = SupplyMatchQuery(sku="CF230A")
    candidate = _candidate(sku="CF230A")

    assert await resolver.resolve(candidate, query, for_ui_display=False) is True
    assert gateway.description_calls == []


# --- consumable_serial (caso real 0BLRBJLJ400006W, ago-2026) ---------------------------


def test_pedido_propio_con_mismo_sku_pero_otra_serie_de_consumible_no_matchea() -> None:
    """3 drums de color con un único SKU compartido en el catálogo de CD: el SKU
    coincide pero son piezas físicas distintas — la serie desempata."""
    own = ProcessedRequest(
        hp_request_id=1,
        internal_order_id="441448-7",
        sku="CF230A",
        consumable_serial="CRUM-0000-5050",
    )
    query = SupplyMatchQuery(
        sku="CF230A", own_orders=(own,), consumable_serial="CRUM-0000-6917"
    )
    assert supply_matches_request(_candidate(), query, for_ui_display=True) is False
    # Anti-duplicado (poller/carga) también respeta la distinción de serie.
    assert supply_matches_request(_candidate(), query, for_ui_display=False) is False


def test_pedido_propio_con_misma_serie_de_consumible_matchea() -> None:
    own = ProcessedRequest(
        hp_request_id=1,
        internal_order_id="441448-7",
        sku="CF230A",
        consumable_serial="CRUM-0000-6917",
    )
    query = SupplyMatchQuery(
        sku="CF230A", own_orders=(own,), consumable_serial="CRUM-0000-6917"
    )
    assert supply_matches_request(_candidate(), query, for_ui_display=True) is True


def test_sin_consumable_serial_de_un_lado_no_bloquea_por_serie() -> None:
    """None en cualquiera de los dos lados: no hay dato para desempatar, sigue el
    camino normal (SKU)."""
    own = _own("441448-7", sku="CF230A")
    query = SupplyMatchQuery(sku="CF230A", own_orders=(own,), consumable_serial="CRUM-0000-6917")
    assert supply_matches_request(_candidate(), query, for_ui_display=True) is True


# --- fallback por tipo sin color (waste/staples) ----------------------------------------


def test_waste_container_sin_sku_ni_color_matchea_por_tipo() -> None:
    """Caso real: pedido "Toner Collection Unit" sin SKU en CD no vinculaba con la
    solicitud "Unidad de recogida de tóner" (Glenmark/MXBCR7N0WC, ago-2026)."""
    candidate = _candidate(sku="", description="Toner Collection Unit")
    query = SupplyMatchQuery(sku="", description="Unidad de recogida de tóner")
    assert supply_matches_request(candidate, query, for_ui_display=True) is True


def test_staples_sin_sku_ni_color_matchea_por_tipo() -> None:
    candidate = _candidate(sku="", description="Staple Cartridge")
    query = SupplyMatchQuery(sku="", description="Cartucho de grapas")
    assert supply_matches_request(candidate, query, for_ui_display=True) is True


def test_toner_sin_sku_ni_color_no_matchea_por_tipo() -> None:
    """toner/drum/developer quedan afuera del fallback por tipo: sí pueden convivir en
    varios colores por equipo, a diferencia de waste/staples."""
    candidate = _candidate(sku="", description="Toner Cartridge")
    query = SupplyMatchQuery(sku="", description="Cartucho de tóner")
    assert supply_matches_request(candidate, query, for_ui_display=True) is False
    assert supply_matches_request(candidate, query, for_ui_display=False) is True


def test_waste_vs_staples_no_matchea() -> None:
    candidate = _candidate(sku="", description="Waste Container")
    query = SupplyMatchQuery(sku="", description="Cartucho de grapas")
    assert supply_matches_request(candidate, query, for_ui_display=True) is False
