"""HttpxHpPortalGateway con transporte mockeado: login con TTL de sesión, búsqueda
de equipo, event logs, EWS remoto, operaciones, refresh de caché y solución."""

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from src.modules.analisis_log_hp.infrastructure.hp_portal import httpx_hp_portal_gateway as mod
from src.modules.analisis_log_hp.infrastructure.hp_portal.httpx_hp_portal_gateway import (
    HttpxHpPortalGateway,
)
from src.shared.domain.errors import ExternalServiceError

Handler = Callable[[httpx.Request], httpx.Response | None]
_BASE = "https://hp-sds-latam.insightportal.net/PortalWeb"


def _patch_transport(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> list[httpx.Request]:
    seen: list[httpx.Request] = []
    real = httpx.AsyncClient

    def routed(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        resp = handler(request)
        return resp if resp is not None else httpx.Response(404)

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("timeout", None)
        return real(transport=httpx.MockTransport(routed), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    return seen


def _login_ok(request: httpx.Request) -> httpx.Response | None:
    if request.url.path == "/PortalWeb/login" and request.method == "GET":
        return httpx.Response(200, text="<form/>")
    if request.url.path == "/PortalWeb/login" and request.method == "POST":
        assert b"username=user" in request.content
        return httpx.Response(302, headers={"Location": f"{_BASE}/home"})
    if request.url.path == "/PortalWeb/home":
        return httpx.Response(200, text="bienvenido")
    return None


def _gateway(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> tuple[
    HttpxHpPortalGateway, list[httpx.Request]
]:
    seen = _patch_transport(monkeypatch, handler)
    return HttpxHpPortalGateway(username="user", password="pass"), seen


class TestLogin:
    async def test_sin_credenciales_falla_antes_de_pegarle_al_portal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = _patch_transport(monkeypatch, lambda r: None)
        gw = HttpxHpPortalGateway(username="", password="")
        with pytest.raises(ExternalServiceError, match="SDS_PORTAL_USERNAME"):
            await gw.get_hp_operations("1")
        assert seen == []

    async def test_redirigido_de_vuelta_al_login_es_credenciales_invalidas(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/login":
                return httpx.Response(200, text="<form/>")
            return None

        gw, _ = _gateway(monkeypatch, handler)
        with pytest.raises(ExternalServiceError, match="Login al portal SDS fallido"):
            await gw.get_hp_operations("1")

    async def test_sesion_vigente_no_relogea(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path.endswith("/operations/refresh"):
                return httpx.Response(200, text="<table></table>")
            return _login_ok(request)

        gw, seen = _gateway(monkeypatch, handler)
        await gw.get_hp_operations("1")
        await gw.get_hp_operations("1")
        logins = [r for r in seen if r.url.path == "/PortalWeb/login" and r.method == "POST"]
        assert len(logins) == 1

    async def test_sesion_vencida_relogea(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path.endswith("/operations/refresh"):
                return httpx.Response(200, text="<table></table>")
            return _login_ok(request)

        gw, seen = _gateway(monkeypatch, handler)
        await gw.get_hp_operations("1")
        monkeypatch.setattr(mod, "_SESSION_TTL", 0)
        await gw.get_hp_operations("1")
        logins = [r for r in seen if r.url.path == "/PortalWeb/login" and r.method == "POST"]
        assert len(logins) == 2


class TestSearchDevice:
    async def test_redireccion_a_devices_da_id_y_modelo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/search":
                assert request.url.params["q"] == "ABC"
                return httpx.Response(302, headers={"Location": f"{_BASE}/devices/4242"})
            if request.url.path == "/PortalWeb/devices/4242":
                return httpx.Response(
                    200,
                    text='<a class="entity-name model" href="#">  HP LaserJet   M404 </a>',
                )
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.search_device("ABC") == {"id": "4242", "model_name": "HP LaserJet M404"}

    async def test_sin_redireccion_busca_id_en_el_html_y_modelo_por_xpath(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/search":
                return httpx.Response(
                    200,
                    text='<a class="x entity-name model" title="t"><b>Modelo B</b></a>'
                    '<a href="/PortalWeb/devices/99">ver</a>',
                )
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.search_device("ABC") == {"id": "99", "model_name": "Modelo B"}

    async def test_sin_device_id_es_equipo_no_encontrado(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/search":
                return httpx.Response(200, text="<p>sin resultados</p>")
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        with pytest.raises(ExternalServiceError, match="no encontrado"):
            await gw.search_device("ABC")


_TABLA = (
    '<response><content><![CDATA[<table class="data"><tbody>'
    "<tr><td>Error</td><td>13.20</td><td>05-ago-2026 09:05:00</td><td>1</td><td>FW</td>"
    '<td><a href="http://h/13">Atasco</a></td></tr></tbody></table>]]></content></response>'
)


class TestEventLogsYEws:
    async def test_fetch_event_logs_devuelve_tsv_y_help_urls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/devices/7/hpsmart/eventlogs":
                assert request.headers["x-requested-with"] == "XMLHttpRequest"
                assert request.url.params.get_list("eventLevel") == ["info", "warning", "error"]
                return httpx.Response(200, text=_TABLA)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        result = await gw.fetch_event_logs("7", days=10)
        assert "Error\t13.20\t05-ago-2026 09:05:00\t1\tFW\tAtasco" in result.tsv
        assert result.help_urls == {"13.20": {"url": "http://h/13", "description": "Atasco"}}

    async def test_fetch_event_logs_con_status_no_200_falla(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if "eventlogs" in request.url.path:
                return httpx.Response(500)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        with pytest.raises(ExternalServiceError, match="500"):
            await gw.fetch_event_logs("7")

    async def test_fetch_remote_ews_url_extrae_el_link(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/devices/7/hpsmart/ews":
                return httpx.Response(
                    200,
                    text='<r><content><![CDATA[<div id="remoteEWSLaunchLink">'
                    '<a href="https://ews.hpjamservices.com/x?jwt=1">abrir</a></div>]]>'
                    "</content></r>",
                )
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.fetch_remote_ews_url("7") == "https://ews.hpjamservices.com/x?jwt=1"

    async def test_fetch_remote_ews_sin_link_devuelve_none_y_error_si_falla(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response | None:
            if request.url.path == "/PortalWeb/devices/7/hpsmart/ews":
                return httpx.Response(200, text="<div>nada</div>")
            if request.url.path == "/PortalWeb/devices/8/hpsmart/ews":
                return httpx.Response(403)
            return _login_ok(request)

        gw, _ = _gateway(monkeypatch, handler)
        assert await gw.fetch_remote_ews_url("7") is None
        with pytest.raises(ExternalServiceError, match="403"):
            await gw.fetch_remote_ews_url("8")
