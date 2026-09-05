"""Gateway httpx de OSRM (table + annotations=distance): orden lon,lat, ida por
fila y vuelta por columna, `None` sin ruta, y fallos → ExternalServiceError.
Sin red: httpx.MockTransport inyectado en el módulo."""

import types
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from src.modules.liquidaciones.infrastructure.osrm import httpx_osrm_gateway
from src.modules.liquidaciones.infrastructure.osrm.httpx_osrm_gateway import HttpxOsrmGateway
from src.shared.domain.errors import ExternalServiceError

Handler = Callable[[httpx.Request], httpx.Response]


def _inyectar(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> None:
    transport = httpx.MockTransport(handler)

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, **kwargs)

    monkeypatch.setattr(
        httpx_osrm_gateway,
        "httpx",
        types.SimpleNamespace(
            AsyncClient=factory,
            HTTPError=httpx.HTTPError,
            HTTPStatusError=httpx.HTTPStatusError,
        ),
    )

    async def sin_pausa(_: float) -> None:
        return None

    monkeypatch.setattr(httpx_osrm_gateway.asyncio, "sleep", sin_pausa)


@pytest.mark.asyncio
async def test_ida_y_vuelta_en_km_con_none_sin_ruta(monkeypatch: pytest.MonkeyPatch) -> None:
    pedidos: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        pedidos.append(str(request.url))
        if "sources=0" in str(request.url):
            body = {"code": "Ok", "distances": [[0, 12500.0, None]]}
        else:
            body = {"code": "Ok", "distances": [[0], [13100.0], [None]]}
        return httpx.Response(200, json=body)

    _inyectar(monkeypatch, handler)
    gw = HttpxOsrmGateway("https://osrm.example")

    tramos = await gw.distancias_km_ida_vuelta((-31.5, -68.5), [(-31.6, -68.6), (-31.7, -68.7)])

    assert tramos == [(12.5, 13.1), (None, None)]
    # lon,lat y anotación de distancia en la URL
    assert "/table/v1/driving/-68.5,-31.5;-68.6,-31.6;-68.7,-31.7" in pedidos[0]
    assert "annotations=distance" in pedidos[0]
    assert "destinations=0" in pedidos[1]


@pytest.mark.asyncio
async def test_code_no_ok_es_external_service_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(monkeypatch, lambda r: httpx.Response(200, json={"code": "NoTable"}))
    with pytest.raises(ExternalServiceError):
        await HttpxOsrmGateway("https://osrm.example").distancias_km((0, 0), [(1, 1)])


@pytest.mark.asyncio
async def test_http_error_es_external_service_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(monkeypatch, lambda r: httpx.Response(503, text="down"))
    with pytest.raises(ExternalServiceError):
        await HttpxOsrmGateway("https://osrm.example").distancias_km((0, 0), [(1, 1)])
