"""Nominatim search como GeocodingGateway: mapeo al vocabulario de Google
(location_type, tipos, partial_match) y fallos → ExternalServiceError. Sin red."""

import types
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.geocoding import httpx_nominatim_geocoding_gateway as mod
from src.shared.infrastructure.geocoding.httpx_nominatim_geocoding_gateway import (
    HttpxNominatimGeocodingGateway,
)

Handler = Callable[[httpx.Request], httpx.Response]


def _inyectar(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> None:
    transport = httpx.MockTransport(handler)

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, **kwargs)

    monkeypatch.setattr(
        mod,
        "httpx",
        types.SimpleNamespace(
            AsyncClient=factory,
            HTTPError=httpx.HTTPError,
            HTTPStatusError=httpx.HTTPStatusError,
        ),
    )


def _resultado(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "lat": "-38.7183",
        "lon": "-62.2663",
        "display_name": "Alsina 100, Bahía Blanca, Buenos Aires, Argentina",
        "class": "place",
        "type": "house",
        "addresstype": "place",
        "address": {"house_number": "100", "road": "Alsina", "city": "Bahía Blanca"},
    }
    base.update(over)
    return base


@pytest.mark.asyncio
async def test_direccion_con_altura_resuelta_es_rooftop(monkeypatch: pytest.MonkeyPatch) -> None:
    urls: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        urls.append(str(req.url))
        assert req.headers["User-Agent"].startswith("HelpDeskManager")
        return httpx.Response(200, json=[_resultado()])

    _inyectar(monkeypatch, handler)
    cands = await HttpxNominatimGeocodingGateway("https://osm.example").geocode(
        "Alsina 100, Bahía Blanca, Buenos Aires, Argentina"
    )

    assert len(cands) == 1
    assert cands[0].location_type == "ROOFTOP"
    assert cands[0].partial_match is False
    assert (cands[0].latitud, cands[0].longitud) == (-38.7183, -62.2663)
    assert "countrycodes=ar" in urls[0] and "addressdetails=1" in urls[0]


@pytest.mark.asyncio
async def test_calle_entera_es_route_y_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(
        monkeypatch,
        lambda r: httpx.Response(
            200,
            json=[
                _resultado(
                    **{
                        "class": "highway",
                        "type": "residential",
                        "addresstype": "road",
                        "address": {"road": "Alsina"},
                    }
                )
            ],
        ),
    )
    cands = await HttpxNominatimGeocodingGateway().geocode("Alsina 100, Bahía Blanca, Argentina")
    assert cands[0].location_type == "GEOMETRIC_CENTER"
    assert cands[0].partial_match is True
    assert "highway" in cands[0].tipos


@pytest.mark.asyncio
async def test_poi_por_nombre_es_rooftop_sin_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(
        monkeypatch,
        lambda r: httpx.Response(
            200,
            json=[
                _resultado(
                    **{
                        "class": "aeroway",
                        "type": "aerodrome",
                        "addresstype": "aeroway",
                        "address": {"city": "Bahía Blanca"},
                    }
                )
            ],
        ),
    )
    cands = await HttpxNominatimGeocodingGateway().geocode("Aeropuerto Bahía Blanca, Argentina")
    assert cands[0].location_type == "ROOFTOP"
    assert cands[0].partial_match is False


@pytest.mark.asyncio
async def test_sin_resultados_lista_vacia(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(monkeypatch, lambda r: httpx.Response(200, json=[]))
    assert await HttpxNominatimGeocodingGateway().geocode("Nada 1, Ningún lado, Argentina") == []


@pytest.mark.asyncio
async def test_http_error_es_external_service_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _inyectar(monkeypatch, lambda r: httpx.Response(429, text="slow down"))
    with pytest.raises(ExternalServiceError):
        await HttpxNominatimGeocodingGateway().geocode("Alsina 100, Bahía Blanca, Argentina")
