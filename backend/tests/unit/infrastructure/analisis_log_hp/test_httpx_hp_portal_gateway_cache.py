"""HttpxHpPortalGateway (parte 2): operaciones HP Smart, refresh de caché con
baseline + CSRF, y fetch de contenido de solución."""

import httpx
import pytest

from src.shared.domain.errors import ExternalServiceError
from tests.unit.infrastructure.analisis_log_hp.test_httpx_hp_portal_gateway import (
    _gateway,
    _login_ok,
)

_OPS = (
    "<table><tr><td>RefreshHPCloudDeviceActionCache</td><td>ayer</td><td>yo</td><td>ok</td></tr>"
    "<tr><td>OtraOperacion</td><td>hoy</td><td>yo</td><td>ok</td></tr></table>"
)
_PANEL = (
    '<form action="/PortalWeb/devices/7/hpsmart/refresh/hpcache" method="post">'
    '<input name="__csrftoken" value="tok123"/></form>'
)


class TestOperacionesYRefresh:
    async def test_get_hp_operations_parsea_la_tabla(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/devices/7/hpsmart/operations/refresh":
                return httpx.Response(200, text=_OPS)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        ops = await gw.get_hp_operations("7")
        assert [o["operation"] for o in ops] == ["RefreshHPCloudDeviceActionCache", "OtraOperacion"]

    async def test_get_hp_operations_con_error_http_falla(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if "operations/refresh" in request.url.path:
                return httpx.Response(502)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        with pytest.raises(ExternalServiceError, match="502"):
            await gw.get_hp_operations("7")

    async def test_refresh_hp_cache_postea_con_csrf_y_devuelve_baseline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/devices/7/hpsmart/operations/refresh":
                return httpx.Response(200, text=_OPS)
            if request.url.path == "/PortalWeb/devices/7/hpsmart":
                return httpx.Response(200, text=_PANEL)
            if request.url.path == "/PortalWeb/devices/7/hpsmart/refresh/hpcache":
                assert request.method == "POST"
                assert b"__csrftoken=tok123" in request.content
                return httpx.Response(204)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        baseline = await gw.refresh_hp_cache("7")
        assert baseline == [{"operation": "RefreshHPCloudDeviceActionCache", "sent": "ayer"}]

    async def test_refresh_sin_operaciones_previas_igual_dispara(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path.endswith("/operations/refresh"):
                return httpx.Response(500)
            if request.url.path == "/PortalWeb/devices/7/hpsmart":
                return httpx.Response(
                    200, text='<form action="https://x/hpsmart/refresh/hpcache"></form>'
                )
            if request.url.path == "/hpsmart/refresh/hpcache":
                assert request.url.host == "x"
                return httpx.Response(200)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.refresh_hp_cache("7") == []

    async def test_refresh_sin_formulario_falla(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path.endswith("/operations/refresh"):
                return httpx.Response(200, text="")
            if request.url.path == "/PortalWeb/devices/7/hpsmart":
                return httpx.Response(200, text="<div>sin form</div>")
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        with pytest.raises(ExternalServiceError, match="no está disponible"):
            await gw.refresh_hp_cache("7")

    async def test_refresh_panel_no_200_falla(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path.endswith("/operations/refresh"):
                return httpx.Response(200, text="")
            if request.url.path == "/PortalWeb/devices/7/hpsmart":
                return httpx.Response(500)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        with pytest.raises(ExternalServiceError, match="panel hpsmart"):
            await gw.refresh_hp_cache("7")

    async def test_refresh_post_rechazado_falla(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path.endswith("/operations/refresh"):
                return httpx.Response(200, text="")
            if request.url.path == "/PortalWeb/devices/7/hpsmart":
                return httpx.Response(200, text=_PANEL)
            if request.url.path.endswith("/refresh/hpcache"):
                return httpx.Response(403)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        with pytest.raises(ExternalServiceError, match="403"):
            await gw.refresh_hp_cache("7")


class TestFetchSolutionContent:
    async def test_devuelve_el_html_si_responde_200_fuera_del_login(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/solucion":
                return httpx.Response(200, text="<p>solución</p>")
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.fetch_solution_content("https://hp/solucion") == "<p>solución</p>"

    async def test_redireccion_al_login_o_error_http_devuelve_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/privada":
                return httpx.Response(302, headers={"Location": "https://hp/login?next=1"})
            if request.url.path == "/login" and request.url.host == "hp":
                return httpx.Response(200, text="login")
            if request.url.path == "/rota":
                return httpx.Response(500)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.fetch_solution_content("https://hp/privada") is None
        assert await gw.fetch_solution_content("https://hp/rota") is None

    async def test_error_de_red_devuelve_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/caida":
                raise httpx.ConnectError("sin red")
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.fetch_solution_content("https://hp/caida") is None
