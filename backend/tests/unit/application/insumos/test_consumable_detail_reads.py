"""Tests de los reads de detalle de consumible: historial de nivel, historial de
solicitudes, ventanas de conectividad y detalle en vivo."""

import pytest

from src.modules.insumos.application.use_cases.get_availability_windows import (
    GetAvailabilityWindows,
)
from src.modules.insumos.application.use_cases.get_consumable_detail import GetConsumableDetail
from src.modules.insumos.application.use_cases.get_consumable_history import (
    GetConsumableHistory,
)
from src.modules.insumos.application.use_cases.get_consumable_request_history import (
    GetConsumableRequestHistory,
)
from src.shared.domain.errors import NotFoundError
from tests.unit.domain.insumos.fakes import FakeInsightGateway

DEVICE_ID = 7
INDEX = 1


async def test_historial_de_nivel_queda_en_orden_cronologico() -> None:
    """Insight devuelve más reciente primero; el gráfico necesita cronológico. Los
    pasos sin recordDate se descartan."""
    insight = FakeInsightGateway()
    insight.history_by_device[DEVICE_ID] = [
        {"recordDate": "2026-08-01T00:00:00Z", "level": 5},
        {"recordDate": "2026-07-01T00:00:00Z", "level": 40},
        {"level": 80},  # sin fecha: afuera
    ]

    points = await GetConsumableHistory(insight).execute(DEVICE_ID, INDEX)  # type: ignore[arg-type]

    assert [(p.date, p.level) for p in points] == [
        ("2026-07-01T00:00:00Z", 40),
        ("2026-08-01T00:00:00Z", 5),
    ]


async def test_historial_de_solicitudes_filtra_dedupe_y_traduce_estados() -> None:
    """Insight no filtra por deviceId del lado del servidor: se piden los 6
    workflowStatus y se filtra acá por equipo + índice, deduplicando por id."""
    insight = FakeInsightGateway()
    mine = {
        "id": 974325,
        "deviceId": DEVICE_ID,
        "consumable": {"index": INDEX},
        "requested": "2026-08-01T10:00:00Z",
        "status": "NEW",
        "requestedLevel": 12,
    }
    insight.requests_by_status = {
        "OUTSTANDING": [mine, {"id": 1, "deviceId": 99, "consumable": {"index": INDEX}}],
        "COMPLETED": [
            mine,  # duplicada entre estados: una sola vez
            {
                "id": 974000,
                "deviceId": DEVICE_ID,
                "consumable": {"index": INDEX},
                "requested": "2026-07-01T10:00:00Z",
                "status": "COMPLETED",
            },
            {"id": 2, "deviceId": DEVICE_ID, "consumable": {"index": 9}},
        ],
    }

    rows = await GetConsumableRequestHistory(insight).execute(  # type: ignore[arg-type]
        DEVICE_ID, INDEX, customer_id=8
    )

    assert [r.request_id for r in rows] == [974325, 974000]  # más reciente primero
    assert rows[0].status_label == "Nuevo"
    assert rows[1].status_label == "Completada"
    assert rows[0].requested_level == 12


async def test_ventanas_de_conectividad_salen_de_las_alertas_availability() -> None:
    insight = FakeInsightGateway()
    insight.alerts_by_device[DEVICE_ID] = [
        {
            "date": "2026-01-18T10:00:00Z",
            "description": "Device busy/unavailable for over 24 hours",
        },
        {"date": "2026-01-19T10:00:00Z", "description": "Monitoring resumed"},
    ]

    windows = await GetAvailabilityWindows(insight).execute(DEVICE_ID)  # type: ignore[arg-type]

    assert len(windows) == 1
    assert windows[0].start == "2026-01-18T10:00:00+00:00"


async def test_detalle_combina_equipo_consumible_y_ciclos_del_historial() -> None:
    insight = FakeInsightGateway()
    insight.devices_by_id[DEVICE_ID] = {
        "extendedFields": {"mibDescription": "HP LaserJet E52645"}
    }
    insight.consumables_by_device[DEVICE_ID] = [
        {"index": 9, "sku": "OTRO"},
        {
            "index": INDEX,
            "type": "TONER",
            "colour": "BLACK",
            "sku": "W9008MC",
            "yield": 23000,
            "reorderPart": {"sku": "W9008MC-R", "yield": 23000},
            "maxLevel": 100,
            "percentLeft": 12,
            "daysLeft": 3,
            "pagesLeft": 2760,
            "lastRead": "2026-08-09T10:00:00Z",
            "engineCyclesMonitored": 5000,
        },
    ]
    insight.history_by_device[DEVICE_ID] = [
        {"recordDate": "2026-08-09T00:00:00Z", "engineCycles": 123456},  # más reciente primero
        {"recordDate": "2026-08-08T00:00:00Z", "engineCycles": 123000},
    ]

    detail = await GetConsumableDetail(insight).execute(DEVICE_ID, INDEX)  # type: ignore[arg-type]

    assert detail.model == "HP LaserJet E52645"
    assert detail.sku == "W9008MC"
    assert detail.reorder_sku == "W9008MC-R"
    assert detail.engine_cycles == 123456  # del historial, no engineCyclesMonitored
    assert detail.engine_cycles_monitored == 5000


async def test_detalle_de_consumible_inexistente_es_not_found() -> None:
    insight = FakeInsightGateway()
    insight.devices_by_id[DEVICE_ID] = {}
    insight.consumables_by_device[DEVICE_ID] = [{"index": 9}]

    with pytest.raises(NotFoundError):
        await GetConsumableDetail(insight).execute(DEVICE_ID, INDEX)  # type: ignore[arg-type]


async def test_fallo_del_historial_no_tira_el_detalle() -> None:
    """engine_cycles es best-effort: sin ese dato el panel se muestra igual."""
    insight = FakeInsightGateway()
    insight.devices_by_id[DEVICE_ID] = {}
    insight.consumables_by_device[DEVICE_ID] = [{"index": INDEX, "sku": "W9008MC"}]
    insight.history_error = ConnectionError("timeout")

    detail = await GetConsumableDetail(insight).execute(DEVICE_ID, INDEX)  # type: ignore[arg-type]

    assert detail.sku == "W9008MC"
    assert detail.engine_cycles is None
