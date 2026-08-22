"""HttpxWatiGateway con transporte mockeado: URL/headers, parseo de las
respuestas de getContacts/getMessages, errores envueltos en
ExternalServiceError y el espaciado entre llamadas (rate limit)."""

import time
from typing import Any

import httpx
import pytest

from src.modules.wati.infrastructure.wati_api.httpx_wati_gateway import HttpxWatiGateway
from src.shared.domain.errors import ExternalServiceError

_BASE = "https://live-mt-server.wati.io"
_CONTACTO = {
    "wAid": "5491130648978",
    "fullName": "Tienda 0649",
    "lastUpdated": "2026-08-21T13:27:04Z",
}
_MENSAJE = {
    "eventType": "message",
    "owner": False,
    "operatorName": "MDA",
    "created": "2026-08-21T15:57:06Z",
    "text": "hola",
}


def _patch_transport(monkeypatch: pytest.MonkeyPatch, handler: Any) -> None:
    real = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("timeout", None)
        return real(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def _gateway(spacing_seconds: float = 0.0, **overrides: Any) -> HttpxWatiGateway:
    kwargs: dict[str, Any] = {"base_url": _BASE + "/", "tenant_id": "123", "token": "tok"}
    kwargs.update(overrides)
    return HttpxWatiGateway(spacing_seconds=spacing_seconds, **kwargs)


async def test_list_contactos_pega_en_get_contacts_con_auth_y_user_agent_propio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"contact_list": [_CONTACTO]})

    _patch_transport(monkeypatch, handler)

    contactos = await _gateway().list_contactos_recientes(limite=40)

    (req,) = requests
    assert str(req.url) == f"{_BASE}/123/api/v1/getContacts?pageSize=40&pageNumber=1"
    assert req.headers["authorization"] == "Bearer tok"
    assert req.headers["user-agent"].startswith("helpdesk-manager/")
    assert [c.wa_id for c in contactos] == ["5491130648978"]


async def test_list_contactos_descarta_items_invalidos_y_tolera_lista_nula(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    respuestas = iter(
        [
            httpx.Response(200, json={"contact_list": [_CONTACTO, {"wAid": "sin fecha"}]}),
            httpx.Response(200, json={"contact_list": None}),
        ]
    )
    _patch_transport(monkeypatch, lambda request: next(respuestas))
    gateway = _gateway()

    con_invalido = await gateway.list_contactos_recientes(limite=10)
    vacio = await gateway.list_contactos_recientes(limite=10)

    assert len(con_invalido) == 1
    assert vacio == []


async def test_get_eventos_pega_en_get_messages_del_wa_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"messages": {"items": [_MENSAJE, {"eventType": "call"}]}})

    _patch_transport(monkeypatch, handler)

    eventos = await _gateway().get_eventos("549", limite=30)

    (req,) = requests
    assert req.url.path == "/123/api/v1/getMessages/549"
    assert req.url.params["pageSize"] == "30"
    assert [e.texto for e in eventos] == ["hola"]


async def test_get_eventos_sin_messages_devuelve_vacio(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json={"messages": None}))

    assert await _gateway().get_eventos("549", limite=30) == []


@pytest.mark.parametrize(("tenant_id", "token"), [("", "tok"), ("123", ""), ("", "")])
async def test_sin_tenant_o_token_falla_sin_llamar(
    monkeypatch: pytest.MonkeyPatch, tenant_id: str, token: str
) -> None:
    llamadas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal llamadas
        llamadas += 1
        return httpx.Response(200, json={})

    _patch_transport(monkeypatch, handler)
    gateway = _gateway(tenant_id=tenant_id, token=token)

    with pytest.raises(ExternalServiceError, match="WATI_TENANT_ID"):
        await gateway.list_contactos_recientes(limite=1)
    assert llamadas == 0


async def test_status_distinto_de_200_se_envuelve_con_detalles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(403, text="Forbidden por UA"))

    with pytest.raises(ExternalServiceError, match="403") as exc_info:
        await _gateway().list_contactos_recientes(limite=1)

    assert exc_info.value.details == {"status": 403, "body": "Forbidden por UA"}


async def test_cuerpo_que_no_es_objeto_json_se_envuelve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json=["lista"]))

    with pytest.raises(ExternalServiceError, match="cuerpo inesperado"):
        await _gateway().get_eventos("549", limite=1)


async def test_error_de_red_se_envuelve(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    _patch_transport(monkeypatch, handler)

    with pytest.raises(ExternalServiceError, match="WATI no responde"):
        await _gateway().list_contactos_recientes(limite=1)


async def test_espacia_las_llamadas_consecutivas(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json={}))
    gateway = _gateway(spacing_seconds=0.05)

    await gateway.list_contactos_recientes(limite=1)
    inicio = time.monotonic()
    await gateway.list_contactos_recientes(limite=1)

    assert time.monotonic() - inicio >= 0.04
