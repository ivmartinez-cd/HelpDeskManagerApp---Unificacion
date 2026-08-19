"""HttpxNominatimGateway: reverse geocoding con rate limit estricto de 1 req/s
(política de uso de Nominatim)."""

import time

import httpx
import pytest

from src.modules.liquidaciones.infrastructure.nominatim.httpx_nominatim_gateway import (
    HttpxNominatimGateway,
)
from src.shared.domain.errors import ExternalServiceError

_RESULTADO_SAN_JUAN = {
    "address": {"state": "San Juan", "country": "Argentina"},
}
_SIN_RESULTADO = {"error": "Unable to geocode"}


def _gateway(handler) -> HttpxNominatimGateway:  # type: ignore[no-untyped-def]
    return HttpxNominatimGateway(transport=httpx.MockTransport(handler))


class TestReverse:
    @pytest.mark.asyncio
    async def test_reverse_con_resultado(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["user-agent"] == "HelpDeskManager-CanalDirecto-Geovalidacion/1.0"
            return httpx.Response(200, json=_RESULTADO_SAN_JUAN)

        ubicacion = await _gateway(handler).reverse(-31.5375, -68.5364)
        assert ubicacion is not None
        assert ubicacion.provincia_nombre == "San Juan"

    @pytest.mark.asyncio
    async def test_sin_resultado_devuelve_none(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_SIN_RESULTADO)

        assert await _gateway(handler).reverse(-40.0, -30.0) is None

    @pytest.mark.asyncio
    async def test_error_500_propaga_sin_reintentar(self) -> None:
        llamadas = []

        def handler(request: httpx.Request) -> httpx.Response:
            llamadas.append(1)
            return httpx.Response(500)

        with pytest.raises(ExternalServiceError):
            await _gateway(handler).reverse(-31.5, -68.5)
        assert len(llamadas) == 1  # sin backoff acá — Nominatim es más estricto

    @pytest.mark.asyncio
    async def test_respeta_rate_limit_de_1_req_por_segundo(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_RESULTADO_SAN_JUAN)

        gateway = _gateway(handler)
        inicio = time.monotonic()
        await gateway.reverse(-31.5, -68.5)
        await gateway.reverse(-31.6, -68.6)
        transcurrido = time.monotonic() - inicio
        assert transcurrido >= 1.0
