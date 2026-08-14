"""HttpxSdsClientProvider con transporte mockeado: login, listado de clientes
y export de contadores a CSV."""

from pathlib import Path
from typing import Any

import httpx
import pytest

from src.modules.contadores.infrastructure.sds.httpx_sds_client_provider import (
    HttpxSdsClientProvider,
    _calculate_min_date,
    _to_max_read_datetime_local,
)
from src.shared.domain.errors import ExternalServiceError
from tests.unit.infrastructure.contadores.settings_stub import make_settings


def _patch_transport(monkeypatch: pytest.MonkeyPatch, handler: Any) -> None:
    real = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("timeout", None)
        return real(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def _provider() -> HttpxSdsClientProvider:
    return HttpxSdsClientProvider(settings=make_settings())


def test_to_max_read_datetime_local_agrega_fin_del_dia() -> None:
    assert _to_max_read_datetime_local("2026-08-14") == "2026-08-14T23:59:59"
    assert _to_max_read_datetime_local("2026-08-14T10:00:00") == "2026-08-14T23:59:59"


def test_calculate_min_date_resta_30_dias_y_tolera_fechas_rotas() -> None:
    minimo = _calculate_min_date("2026-08-31")
    assert minimo is not None and minimo.strftime("%Y-%m-%d") == "2026-08-01"
    assert _calculate_min_date("") is None


def _login_ok(request: httpx.Request) -> httpx.Response | None:
    if request.url.path == "/PortalAPI/login":
        assert request.headers["Authorization"].startswith("Basic ")
        return httpx.Response(200, json={"access_token": "tok-sds"})
    return None


async def test_list_active_customers_filtra_activos_y_ordena(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        login = _login_ok(request)
        if login is not None:
            return login
        assert request.url.path == "/PortalAPI/api/customers"
        assert request.headers["Authorization"] == "Bearer tok-sds"
        return httpx.Response(
            200,
            json=[
                {"id": 2, "name": "Zeta", "status": "active"},
                {"customerId": 1, "name": "Alfa", "status": "ACTIVE"},
                {"id": 3, "name": "Baja", "status": "INACTIVE"},
            ],
        )

    _patch_transport(monkeypatch, handler)

    clients = await _provider().list_active_customers()

    assert [(c.id, c.name) for c in clients] == [("1", "Alfa"), ("2", "Zeta")]


async def test_list_active_customers_error_http(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _login_ok(request) or httpx.Response(502, text="bad gateway")

    _patch_transport(monkeypatch, handler)
    with pytest.raises(ExternalServiceError, match="502"):
        await _provider().list_active_customers()


async def test_login_toma_el_token_del_header_como_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/PortalAPI/login":
            return httpx.Response(200, text="ok", headers={"Authorization": "Bearer del-header"})
        assert request.headers["Authorization"] == "Bearer del-header"
        return httpx.Response(200, json=[])

    _patch_transport(monkeypatch, handler)
    assert await _provider().list_active_customers() == []


async def test_login_sin_token_en_ningun_lado(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json={}))
    with pytest.raises(ExternalServiceError, match="token"):
        await _provider().list_active_customers()


async def test_login_rechazado(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(401, text="no"))
    with pytest.raises(ExternalServiceError, match="401"):
        await _provider().list_active_customers()


async def test_login_error_de_conexion_se_envuelve(monkeypatch: pytest.MonkeyPatch) -> None:
    def explota(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    _patch_transport(monkeypatch, explota)
    with pytest.raises(ExternalServiceError, match="autenticar"):
        await _provider().list_active_customers()


def _export_handler(request: httpx.Request) -> httpx.Response:
    login = _login_ok(request)
    if login is not None:
        return login
    path = request.url.path
    if path == "/PortalAPI/api/devices/meters/latestbydate/c1":
        assert request.url.params["maxReadDateTimeLocal"] == "2026-08-14T23:59:59"
        return httpx.Response(
            200,
            json=[
                {
                    "deviceId": 10,
                    "readingDate": "2026-08-01",
                    "engineCycles": 100,
                    "monoPages": 70,
                    "colourPages": 30,
                },
                {  # fuera del rango de 30 días: se filtra
                    "deviceId": 11,
                    "readingDate": "2026-01-01",
                    "monoPages": 5,
                },
                {  # fecha ilegible: no filtra y usa el valor crudo
                    "deviceId": 12,
                    "readingDate": "fecha-rota",
                    "monoPages": 9,
                },
            ],
        )
    if path == "/PortalAPI/api/devices":
        return httpx.Response(
            200, json=[{"deviceId": 10, "serialNumber": "S10"}, {"otro": "sin id"}]
        )
    return httpx.Response(500, text=f"ruta inesperada {path}")


async def test_export_meters_to_csv_escribe_filas_filtradas(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, _export_handler)

    ruta = await _provider().export_meters_to_csv(
        customer_id="c1",
        customer_name="Cliente Uno",
        max_date="2026-08-14",
        output_dir=str(tmp_path),
    )

    contenido = Path(ruta).read_text(encoding="utf-8")
    assert Path(ruta).name == "SDS_Cliente_Uno_20260814_AutoCSV.csv"
    # El device 10 usa la serie del mapa; color separado en CLASE_20.
    assert "S10;01/08/2026;21;10;70;20;30" in contenido
    # El 11 quedó filtrado por rango; el 12 entra con la fecha cruda y su id como serie.
    assert "2026-01-01" not in contenido
    assert "12;fecha-rota;21;10;9" in contenido


async def test_export_meters_suma_color_usa_engine_cycles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, _export_handler)

    ruta = await _provider().export_meters_to_csv(
        customer_id="c1",
        customer_name="Cliente Uno",
        max_date="2026-08-14",
        output_dir=str(tmp_path),
        suma_color=True,
    )

    contenido = Path(ruta).read_text(encoding="utf-8")
    assert Path(ruta).name.endswith("_SumaColor_AutoCSV.csv")
    assert "S10;01/08/2026;21;20;100" in contenido


async def test_export_meters_sin_contadores(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _login_ok(request) or httpx.Response(200, json=[])

    _patch_transport(monkeypatch, handler)
    with pytest.raises(ExternalServiceError, match="No se encontraron contadores"):
        await _provider().export_meters_to_csv(
            customer_id="c1", customer_name="X", max_date="2026-08-14", output_dir=str(tmp_path)
        )


async def test_serial_map_con_error_http_cae_a_vacio(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        login = _login_ok(request)
        if login is not None:
            return login
        if request.url.path == "/PortalAPI/api/devices":
            return httpx.Response(500, text="boom")
        return httpx.Response(
            200,
            json=[{"deviceId": 10, "readingDate": "2026-08-01", "monoPages": 7}],
        )

    _patch_transport(monkeypatch, handler)

    ruta = await _provider().export_meters_to_csv(
        customer_id="c1", customer_name="X", max_date="2026-08-14", output_dir=str(tmp_path)
    )

    # Sin mapa de series, la fila usa el deviceId crudo como SERIE.
    assert "10;01/08/2026;21;10;7" in Path(ruta).read_text(encoding="utf-8")
