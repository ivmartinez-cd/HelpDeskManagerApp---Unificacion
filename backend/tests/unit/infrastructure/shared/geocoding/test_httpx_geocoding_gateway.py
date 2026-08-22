"""Gateway httpx de Google Geocoding: parseo de la respuesta y traducción de
fallos a ExternalServiceError. Sin red ni key real: httpx.MockTransport
inyectado en el módulo del gateway."""

import types
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.geocoding import httpx_geocoding_gateway
from src.shared.infrastructure.geocoding.httpx_geocoding_gateway import (
    HttpxGeocodingGateway,
)

Handler = Callable[[httpx.Request], httpx.Response]


def _inyectar(monkeypatch: pytest.MonkeyPatch, modulo: Any, handler: Handler) -> None:
    transport = httpx.MockTransport(handler)

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, **kwargs)

    monkeypatch.setattr(
        modulo,
        "httpx",
        types.SimpleNamespace(
            AsyncClient=factory,
            HTTPError=httpx.HTTPError,
            HTTPStatusError=httpx.HTTPStatusError,
        ),
    )


async def test_geocode_parsea_candidatos_y_manda_key(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "Av. Santa Fe 4000, CABA",
                        "geometry": {
                            "location": {"lat": -34.58, "lng": -58.42},
                            "location_type": "ROOFTOP",
                        },
                        "types": ["street_address"],
                        "partial_match": True,
                    },
                    {},
                ],
            },
        )

    _inyectar(monkeypatch, httpx_geocoding_gateway, handler)
    candidatos = await HttpxGeocodingGateway("KEY").geocode("santa fe 4000")

    assert requests[0].url.params["key"] == "KEY"
    assert requests[0].url.params["address"] == "santa fe 4000"
    assert candidatos[0].formatted_address == "Av. Santa Fe 4000, CABA"
    assert (candidatos[0].latitud, candidatos[0].longitud) == (-34.58, -58.42)
    assert candidatos[0].tipos == ("street_address",)
    assert candidatos[0].partial_match is True
    assert candidatos[1].formatted_address == ""
    assert candidatos[1].latitud == 0.0


async def test_zero_results_devuelve_lista_vacia(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(
        monkeypatch,
        httpx_geocoding_gateway,
        lambda r: httpx.Response(200, json={"status": "ZERO_RESULTS", "results": []}),
    )
    assert await HttpxGeocodingGateway("KEY").geocode("nada") == []


async def test_status_no_ok_levanta(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(
        monkeypatch,
        httpx_geocoding_gateway,
        lambda r: httpx.Response(200, json={"status": "REQUEST_DENIED"}),
    )
    with pytest.raises(ExternalServiceError, match="REQUEST_DENIED"):
        await HttpxGeocodingGateway("KEY").geocode("x")


async def test_error_http_y_de_conexion_levantan(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(monkeypatch, httpx_geocoding_gateway, lambda r: httpx.Response(500))
    with pytest.raises(ExternalServiceError, match="HTTP"):
        await HttpxGeocodingGateway("KEY").geocode("x")

    def caido(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red", request=request)

    _inyectar(monkeypatch, httpx_geocoding_gateway, caido)
    with pytest.raises(ExternalServiceError, match="conexión"):
        await HttpxGeocodingGateway("KEY").geocode("x")
