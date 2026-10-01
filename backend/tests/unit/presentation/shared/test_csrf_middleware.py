"""Double-submit CSRF: con sesión, toda mutación exige header == cookie."""

import httpx
import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from src.shared.presentation.middlewares.csrf import CsrfMiddleware


async def _ok(_request: object) -> PlainTextResponse:
    return PlainTextResponse("ok")


def _client(cookies: dict[str, str]) -> httpx.AsyncClient:
    app = Starlette(routes=[Route("/api/x", _ok, methods=["GET", "POST", "DELETE"])])
    app.add_middleware(CsrfMiddleware, session_cookie="hdm_session", csrf_cookie="hdm_csrf")
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t", cookies=cookies
    )


_SESION = {"hdm_session": "s", "hdm_csrf": "token-bueno"}


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-CSRF-Token": "otro"}],
    ids=["sin_header", "header_distinto"],
)
async def test_mutacion_con_sesion_sin_token_valido_es_403(headers: dict[str, str]) -> None:
    async with _client(_SESION) as c:
        response = await c.post("/api/x", headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALIDO"


async def test_mutacion_con_token_igual_a_la_cookie_pasa() -> None:
    async with _client(_SESION) as c:
        assert (await c.delete("/api/x", headers={"X-CSRF-Token": "token-bueno"})).text == "ok"


async def test_lecturas_y_pedidos_sin_sesion_no_se_controlan() -> None:
    async with _client(_SESION) as c:
        assert (await c.get("/api/x")).status_code == 200
    async with _client({}) as c:
        assert (await c.post("/api/x")).status_code == 200


async def test_sesion_sin_cookie_csrf_es_403() -> None:
    async with _client({"hdm_session": "s"}) as c:
        assert (await c.post("/api/x", headers={"X-CSRF-Token": ""})).status_code == 403
