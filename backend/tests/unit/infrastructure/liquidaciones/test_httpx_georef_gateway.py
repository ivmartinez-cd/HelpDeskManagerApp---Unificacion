"""HttpxGeorefGateway: reverse geocoding contra la API Georef, con backoff
acotado ante 429/5xx y sin reintento ante errores no transitorios."""

import httpx
import pytest

from src.modules.liquidaciones.infrastructure.georef.httpx_georef_gateway import (
    HttpxGeorefGateway,
)
from src.shared.domain.errors import ExternalServiceError

_UBICACION_SAN_JUAN = {
    "ubicacion": {
        "lat": -31.5375,
        "lon": -68.5364,
        "provincia": {"id": "70", "nombre": "San Juan"},
        "departamento": {"id": "70028", "nombre": "Capital"},
    }
}
_UBICACION_SIN_COBERTURA = {
    "ubicacion": {
        "lat": 0.0,
        "lon": 0.0,
        "provincia": {"id": None, "nombre": None},
        "departamento": {"id": None, "nombre": None},
    }
}


def _gateway(handler) -> HttpxGeorefGateway:  # type: ignore[no-untyped-def]
    return HttpxGeorefGateway(transport=httpx.MockTransport(handler))


class TestReverse:
    @pytest.mark.asyncio
    async def test_reverse_con_cobertura(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_UBICACION_SAN_JUAN)

        ubicacion = await _gateway(handler).reverse(-31.5375, -68.5364)
        assert ubicacion is not None
        assert ubicacion.provincia_nombre == "San Juan"
        assert ubicacion.departamento_nombre == "Capital"

    @pytest.mark.asyncio
    async def test_reverse_sin_cobertura_devuelve_none(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_UBICACION_SIN_COBERTURA)

        assert await _gateway(handler).reverse(0.0, 0.0) is None

    @pytest.mark.asyncio
    async def test_error_400_no_reintenta(self) -> None:
        llamadas = []

        def handler(request: httpx.Request) -> httpx.Response:
            llamadas.append(1)
            return httpx.Response(400, json={"errores": [{"mensaje": "bad"}]})

        with pytest.raises(ExternalServiceError):
            await _gateway(handler).reverse(999.0, 999.0)
        assert len(llamadas) == 1

    @pytest.mark.asyncio
    async def test_500_persistente_agota_reintentos_y_falla(self) -> None:
        llamadas = []

        def handler(request: httpx.Request) -> httpx.Response:
            llamadas.append(1)
            return httpx.Response(503)

        with pytest.raises(ExternalServiceError):
            await _gateway(handler).reverse(-31.5, -68.5)
        assert len(llamadas) == 3  # intento inicial + 2 reintentos

    @pytest.mark.asyncio
    async def test_429_se_recupera_en_el_segundo_intento(self) -> None:
        llamadas = []

        def handler(request: httpx.Request) -> httpx.Response:
            llamadas.append(1)
            if len(llamadas) == 1:
                return httpx.Response(429)
            return httpx.Response(200, json=_UBICACION_SAN_JUAN)

        ubicacion = await _gateway(handler).reverse(-31.5375, -68.5364)
        assert ubicacion is not None
        assert len(llamadas) == 2
