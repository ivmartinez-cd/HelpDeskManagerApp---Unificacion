"""Telemetría ERS: parseo de fechas, armado de filas CSV y recolección con
transporte mockeado (sin red)."""

from datetime import datetime
from typing import Any

import httpx

from src.modules.contadores.infrastructure.ers.ers_device_telemetry import (
    _build_row,
    _resolve_fecha_csv,
    collect_device_rows,
    parse_max_date,
)

_MIN = datetime(2026, 7, 15)
_MAX = datetime(2026, 8, 14, 23, 59, 59)


def test_parse_max_date_normaliza_al_final_del_dia() -> None:
    assert parse_max_date("2026-08-14") == datetime(2026, 8, 14, 23, 59, 59)
    assert parse_max_date("2026-08-14T10:00:00Z") == datetime(2026, 8, 14, 23, 59, 59)


def test_parse_max_date_ilegible_cae_a_hoy() -> None:
    resultado = parse_max_date("no-es-una-fecha")
    assert (resultado.hour, resultado.minute, resultado.second) == (23, 59, 59)
    assert resultado.date() == datetime.now().date()


def test_resolve_fecha_csv_dentro_y_fuera_de_rango() -> None:
    assert _resolve_fecha_csv("2026-08-01T10:00:00Z", _MIN, _MAX) == (True, "01/08/2026")
    assert _resolve_fecha_csv("2026-06-01T10:00:00Z", _MIN, _MAX) == (False, "")


def test_resolve_fecha_csv_ilegible_no_filtra_y_usa_fallback_crudo() -> None:
    assert _resolve_fecha_csv("fecha-rota-larga", _MIN, _MAX) == (True, "fecha-rota-l"[:10])


def _details(*, lc: int = 0, tp: int = 0, tcp: int = 0) -> dict[str, Any]:
    return {
        "serial_number": "S123",
        "device_info_json": {
            "UsageInfo": {"PrtMarker": {"LC": lc}, "Marker": [{"TP": tp, "TCP": tcp}]}
        },
    }


def test_build_row_mono_usa_clase_10() -> None:
    row = _build_row(_details(lc=100, tcp=0), "14/08/2026", suma_color=False)
    assert row["CLASE_10"] == 10 and row["CONTADOR_10"] == 100
    assert row["CLASE_20"] == "" and row["CONTADOR_20"] == 0


def test_build_row_color_separa_mono_de_color() -> None:
    row = _build_row(_details(lc=100, tcp=30), "14/08/2026", suma_color=False)
    assert row["CONTADOR_10"] == 70 and row["CLASE_20"] == 20 and row["CONTADOR_20"] == 30
    assert row["OBSERVACION"] == "Epson ERS"


def test_build_row_suma_color_todo_en_clase_20() -> None:
    row = _build_row(_details(lc=100, tcp=30), "14/08/2026", suma_color=True)
    assert row["CLASE_10"] == 20 and row["CONTADOR_10"] == 100 and row["CONTADOR_20"] == 0


def test_build_row_sin_lc_reconstruye_el_total_desde_marker() -> None:
    row = _build_row(_details(lc=0, tp=60, tcp=40), "14/08/2026", suma_color=False)
    assert row["CONTADOR_10"] == 60 and row["CONTADOR_20"] == 40


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/devices/ok/statuses/":
        return httpx.Response(
            200,
            json={"items": [{"upload_id": "u1", "collected_datetime": "2026-08-01T10:00:00Z"}]},
        )
    if path == "/devices/ok/statuses/u1/":
        return httpx.Response(200, json=_details(lc=100, tcp=30))
    if path == "/devices/sin-status/statuses/":
        return httpx.Response(200, json={"items": []})
    if path == "/devices/fuera-de-rango/statuses/":
        return httpx.Response(
            200,
            json={"items": [{"upload_id": "u2", "collected_datetime": "2026-01-01T10:00:00Z"}]},
        )
    if path == "/devices/telemetria-rota/statuses/":
        return httpx.Response(
            200,
            json={"items": [{"upload_id": "u3", "collected_datetime": "2026-08-01T10:00:00Z"}]},
        )
    if path == "/devices/telemetria-rota/statuses/u3/":
        return httpx.Response(500, text="boom")
    return httpx.Response(500, text=f"ruta inesperada {path}")


async def test_collect_device_rows_descarta_sin_telemetria_y_fuera_de_rango() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(_handler)) as client:
        rows = await collect_device_rows(
            client=client,
            headers={},
            base_url="https://ers.test",
            device_ids=["ok", "sin-status", "fuera-de-rango", "telemetria-rota"],
            max_dt=_MAX,
            min_dt=_MIN,
            suma_color=False,
        )

    assert len(rows) == 1
    assert rows[0]["SERIE"] == "S123" and rows[0]["FECHA"] == "01/08/2026"


async def test_collect_device_rows_atrapa_errores_de_conexion_por_dispositivo() -> None:
    def explota(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    async with httpx.AsyncClient(transport=httpx.MockTransport(explota)) as client:
        rows = await collect_device_rows(
            client=client,
            headers={},
            base_url="https://ers.test",
            device_ids=["cualquiera"],
            max_dt=_MAX,
            min_dt=_MIN,
            suma_color=False,
        )

    assert rows == []
