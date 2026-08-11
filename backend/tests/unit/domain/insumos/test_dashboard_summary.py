"""Tests de la agregación pura del dashboard (fase 4 de compute_dashboard_state)."""

from datetime import date, datetime

from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.services.dashboard_summary import (
    CustomerRequests,
    RequestSnapshot,
    summarize_customers,
)
from src.modules.insumos.domain.services.supply_request_matching import (
    match_active_supply,
    match_supply_for_request,
)
from src.modules.insumos.domain.value_objects.cd_datetime import CD_TIMEZONE
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings

_SETTINGS = InsumosSettings()  # umbrales 3/7/14


def _snapshot(
    hp_request_id: int,
    days_left: int | None = 10,
    serial: str = "SERIE1",
    sku: str = "CF230A",
    description: str = "Cartucho negro HP 30A",
) -> RequestSnapshot:
    return RequestSnapshot(
        hp_request_id=hp_request_id,
        device_id=7,
        device_serial=serial,
        sku=sku,
        description=description,
        days_left=days_left,
        requested_day=date(2026, 8, 10),
    )


def _data(
    requests: tuple[RequestSnapshot, ...], processed: frozenset[int] = frozenset()
) -> CustomerRequests:
    return CustomerRequests(
        customer_id=8, name="Cliente", requests=requests, processed_ids=processed
    )


def test_severidad_en_los_bordes_de_los_umbrales() -> None:
    requests = (
        _snapshot(1, days_left=3),  # <= 3 → critical
        _snapshot(2, days_left=4),  # (3, 7] → urgent
        _snapshot(3, days_left=14),  # (7, 14] → warning
        _snapshot(4, days_left=15),  # > 14 → good
    )
    per_customer, totals = summarize_customers([_data(requests)], _SETTINGS, {}, {})

    entry = per_customer[0]
    assert (entry.critical, entry.urgent, entry.warning, entry.good) == (1, 1, 1, 1)
    assert totals["pending"] == 4
    assert totals["loaded"] == 0


def test_procesada_cuenta_como_cargada() -> None:
    per_customer, totals = summarize_customers(
        [_data((_snapshot(1),), processed=frozenset({1}))], _SETTINGS, {}, {}
    )
    assert per_customer[0].loaded == 1
    assert totals["pending"] == 0


def test_supply_activo_del_mismo_consumible_cuenta_como_cargada() -> None:
    supplies = {
        "SERIE1": [
            CachedSupply(
                supply_id=441500,
                serial="SERIE1",
                estado="Pendiente",
                description="Cartucho negro HP 30A",
            )
        ]
    }
    per_customer, _ = summarize_customers([_data((_snapshot(1),))], _SETTINGS, supplies, {})
    assert per_customer[0].loaded == 1


def test_supply_sin_datos_no_oculta_la_solicitud_en_la_ui() -> None:
    """Criterio UI (for_ui_display=True): mejor mostrarla pendiente que taparla con un
    pedido que podría ser de otro consumible (caso CN4766M07W)."""
    supplies = {"SERIE1": [CachedSupply(supply_id=441500, serial="SERIE1", estado="Pendiente")]}
    per_customer, _ = summarize_customers([_data((_snapshot(1),))], _SETTINGS, supplies, {})
    assert per_customer[0].pending == 1


def test_orden_por_gravedad_y_nombre() -> None:
    tranquilo = CustomerRequests(
        customer_id=1, name="A Tranquilo", requests=(_snapshot(1, days_left=20),),
        processed_ids=frozenset(),
    )
    critico = CustomerRequests(
        customer_id=2, name="Z Critico", requests=(_snapshot(2, days_left=1),),
        processed_ids=frozenset(),
    )
    per_customer, _ = summarize_customers([tranquilo, critico], _SETTINGS, {}, {})
    assert [e.name for e in per_customer] == ["Z Critico", "A Tranquilo"]


# --- helpers de matching del dashboard -------------------------------------------------


def test_match_active_supply_saltea_entregado() -> None:
    supplies = [
        CachedSupply(supply_id=222, serial="S", estado="Entregado"),
        CachedSupply(supply_id=111, serial="S", estado="Despachado"),
    ]
    active = match_active_supply(supplies)
    assert active is not None
    assert active.supply_id == 111


def test_match_supply_for_request_compara_dia_argentino() -> None:
    supplies = [
        CachedSupply(
            supply_id=111,
            serial="S",
            estado="Pendiente",
            fecha=datetime(2026, 8, 9, 23, 0, tzinfo=CD_TIMEZONE),
        )
    ]
    assert match_supply_for_request(supplies, date(2026, 8, 10)) is None
    assert match_supply_for_request(supplies, date(2026, 8, 9)) is not None
    assert match_supply_for_request(supplies, None) is None


def test_own_order_de_otro_color_no_tapa_la_solicitud() -> None:
    """El supply activo es NUESTRO pedido de otro consumible (bug 441448) — no debe
    contar la solicitud como cargada."""
    supplies = {
        "SERIE1": [CachedSupply(supply_id=441448, serial="SERIE1", estado="Pendiente")]
    }
    own = {
        "SERIE1": [
            ProcessedRequest(hp_request_id=9, internal_order_id="441448-7", sku="W9008MC")
        ]
    }
    per_customer, _ = summarize_customers([_data((_snapshot(1),))], _SETTINGS, supplies, own)
    assert per_customer[0].pending == 1
