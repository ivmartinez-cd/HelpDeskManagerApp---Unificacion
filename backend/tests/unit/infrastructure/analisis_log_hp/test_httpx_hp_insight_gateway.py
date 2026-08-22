"""HttpxHpInsightGateway con httpx.MockTransport: login Basic → Bearer con
refresh por expiración, reintentos en 5xx/429, y el mapeo de cada endpoint."""

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from src.modules.analisis_log_hp.infrastructure.hp_insight import httpx_hp_insight_gateway as mod
from src.modules.analisis_log_hp.infrastructure.hp_insight.httpx_hp_insight_gateway import (
    HttpxHpInsightGateway,
)
from src.shared.domain.errors import ExternalServiceError

Handler = Callable[[httpx.Request], httpx.Response | None]


def _login_ok(request: httpx.Request, *, expires_in: int = 3600) -> httpx.Response | None:
    if request.url.path == "/PortalAPI/login":
        assert request.headers["Authorization"].startswith("Basic ")
        return httpx.Response(200, json={"access_token": "tok", "expires_in": expires_in})
    return None


def _gateway(handler: Handler) -> tuple[HttpxHpInsightGateway, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def routed(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        resp = handler(request)
        return resp if resp is not None else httpx.Response(404, text="sin ruta")

    gw = HttpxHpInsightGateway(
        "https://insight/PortalAPI/", "key", "secret", transport=httpx.MockTransport(routed)
    )
    return gw, seen


class TestToken:
    async def test_login_una_vez_y_bearer_en_las_llamadas(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalAPI/api/customers":
                assert request.headers["Authorization"] == "Bearer tok"
                return httpx.Response(200, json=[{"customerId": 1}])
            return _login_ok(request)

        gw, seen = _gateway(handler)
        await gw.get_customers()
        await gw.get_customers()
        assert [r.url.path for r in seen].count("/PortalAPI/login") == 1

    async def test_token_vencido_relogea(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalAPI/api/customers":
                return httpx.Response(200, json=[])
            return _login_ok(request, expires_in=0)

        gw, seen = _gateway(handler)
        await gw.get_customers()
        await gw.get_customers()
        assert [r.url.path for r in seen].count("/PortalAPI/login") == 2

    async def test_login_rechazado_es_external_service_error(self) -> None:
        gw, _ = _gateway(lambda r: httpx.Response(401, text="no"))
        with pytest.raises(ExternalServiceError, match="401"):
            await gw.get_customers()

    async def test_error_de_red_en_login_es_external_service_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            raise httpx.ConnectError("sin red")

        gw, _ = _gateway(handler)
        with pytest.raises(ExternalServiceError, match="autenticar"):
            await gw.get_customers()


class TestRequestYRetry:
    async def test_reintenta_en_503_y_luego_devuelve(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(mod, "_RETRY_BACKOFF", (0, 0, 0))
        intentos = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalAPI/api/customers":
                intentos["n"] += 1
                if intentos["n"] < 3:
                    return httpx.Response(503)
                return httpx.Response(200, json=[{"customerId": 1}])
            return _login_ok(request)

        gw, _ = _gateway(handler)
        assert await gw.get_customers() == [{"customerId": 1}]
        assert intentos["n"] == 3

    async def test_agota_reintentos_y_falla(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(mod, "_RETRY_BACKOFF", (0, 0, 0))

        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalAPI/api/customers":
                return httpx.Response(429, text="rate")
            return _login_ok(request)

        gw, seen = _gateway(handler)
        with pytest.raises(ExternalServiceError, match="429"):
            await gw.get_customers()
        assert [r.url.path for r in seen].count("/PortalAPI/api/customers") == 4

    async def test_404_no_reintenta_y_falla(self) -> None:
        gw, seen = _gateway(_login_ok)
        with pytest.raises(ExternalServiceError, match="404"):
            await gw.get_customers()
        assert [r.url.path for r in seen].count("/PortalAPI/api/customers") == 1

    async def test_error_de_red_en_request_es_external_service_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalAPI/api/customers":
                raise httpx.ReadTimeout("lento")
            return _login_ok(request)

        gw, _ = _gateway(handler)
        with pytest.raises(ExternalServiceError, match="Error de red"):
            await gw.get_customers()

    async def test_respuesta_no_lista_se_degrada_a_vacio(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalAPI/api/customers":
                return httpx.Response(200, json={"raro": True})
            return _login_ok(request)

        gw, _ = _gateway(handler)
        assert await gw.get_customers() == []


def _json_router(routes: dict[str, Any]) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response | None:
        if request.url.path in routes:
            return httpx.Response(200, json=routes[request.url.path])
        return _login_ok(request)

    return handler


class TestEndpoints:
    @pytest.mark.parametrize(
        ("payload", "esperado"),
        [
            ([{"deviceId": 1}, {"deviceId": 2}], {"deviceId": 1}),
            ([], None),
            ({"deviceId": 3}, {"deviceId": 3}),
            ("texto", None),
        ],
    )
    async def test_search_by_serial_normaliza_la_respuesta(
        self, payload: Any, esperado: dict[str, Any] | None
    ) -> None:
        gw, seen = _gateway(_json_router({"/PortalAPI/api/devices/search": payload}))
        assert await gw.search_by_serial("ABC") == esperado
        req = next(r for r in seen if r.url.path.endswith("/search"))
        assert req.url.params["q"] == "serial:ABC"
        assert req.url.params["includeExtendedFields"] == "true"

    async def test_consumables_extrae_la_lista_o_vacio(self) -> None:
        gw, _ = _gateway(_json_router({
            "/PortalAPI/api/devices/1/consumables": {"consumables": [{"color": "K"}]},
            "/PortalAPI/api/devices/2/consumables": {"otro": 1},
        }))
        assert await gw.get_device_consumables(1) == [{"color": "K"}]
        assert await gw.get_device_consumables(2) == []

    async def test_alertas_metros_y_devices_pasan_los_parametros(self) -> None:
        gw, seen = _gateway(_json_router({
            "/PortalAPI/api/devices/1/alerts/current": [{"a": 1}],
            "/PortalAPI/api/devices/1/alerts/history": [{"h": 1}],
            "/PortalAPI/api/devices/1/meters/history": [{"m": 1}],
            "/PortalAPI/api/devices": [{"deviceId": 1}],
        }))
        assert await gw.get_device_alerts_current(1) == [{"a": 1}]
        assert await gw.get_device_alerts_history(
            1, from_date="2026-01-01", to_date="2026-02-01", max_results=5
        ) == [{"h": 1}]
        assert await gw.get_device_alerts_history(1) == [{"h": 1}]
        assert await gw.get_device_meters_history(1, days=30) == [{"m": 1}]
        assert await gw.get_devices(9) == [{"deviceId": 1}]

        by_path = {r.url.path: r for r in seen}
        hist = [r for r in seen if r.url.path.endswith("/alerts/history")]
        assert dict(hist[0].url.params) == {
            "fromDate": "2026-01-01", "toDate": "2026-02-01", "maxResults": "5"
        }
        assert dict(hist[1].url.params) == {}
        assert by_path["/PortalAPI/api/devices/1/meters/history"].url.params["days"] == "30"
        assert by_path["/PortalAPI/api/devices"].url.params["customerId"] == "9"
