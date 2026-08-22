"""Gateway httpx de Google Distance Matrix: parseo de la respuesta y
traducción de fallos a ExternalServiceError. Sin red ni key real:
httpx.MockTransport inyectado en el módulo del gateway. El de Geocoding se
movió a tests/unit/infrastructure/shared/geocoding/ (es compartido)."""

import types
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from src.modules.liquidaciones.infrastructure.google_maps import (
    httpx_google_maps_gateway,
)
from src.modules.liquidaciones.infrastructure.google_maps.httpx_google_maps_gateway import (
    HttpxGoogleMapsGateway,
)
from src.shared.domain.errors import ExternalServiceError

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


def _elemento(metros: int | None) -> dict[str, Any]:
    if metros is None:
        return {"status": "ZERO_RESULTS"}
    return {"status": "OK", "distance": {"value": metros}}


class TestDistanceMatrix:
    async def test_distancias_km_parsea_elementos_y_none_sin_ruta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={"status": "OK", "rows": [{"elements": [_elemento(12500), _elemento(None)]}]},
            )

        _inyectar(monkeypatch, httpx_google_maps_gateway, handler)
        gateway = HttpxGoogleMapsGateway("KEY")
        assert await gateway.distancias_km((-34.6, -58.4), []) == []
        kms = await gateway.distancias_km((-34.6, -58.4), [(-34.58, -58.42), (0.0, 0.0)])

        assert kms == [12.5, None]
        assert requests[0].url.params["origins"] == "-34.6,-58.4"
        assert requests[0].url.params["destinations"] == "-34.58,-58.42|0.0,0.0"
        assert requests[0].url.params["mode"] == "driving"

    async def test_ida_vuelta_combina_dos_requests(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if "|" in request.url.params["destinations"]:
                # base -> destinos: una fila con N elementos
                rows = [{"elements": [_elemento(10000), _elemento(20000)]}]
            else:
                # destinos -> base: N filas de 1 elemento (la segunda sin ruta)
                rows = [{"elements": [_elemento(11000)]}, {"elements": []}]
            return httpx.Response(200, json={"status": "OK", "rows": rows})

        _inyectar(monkeypatch, httpx_google_maps_gateway, handler)
        gateway = HttpxGoogleMapsGateway("KEY")
        assert await gateway.distancias_km_ida_vuelta((-34.6, -58.4), []) == []
        resultado = await gateway.distancias_km_ida_vuelta(
            (-34.6, -58.4), [(-34.58, -58.42), (-34.50, -58.50)]
        )
        assert resultado == [(10.0, 11.0), (20.0, None)]

    async def test_sin_rows_devuelve_lista_vacia(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _inyectar(
            monkeypatch,
            httpx_google_maps_gateway,
            lambda r: httpx.Response(200, json={"status": "OK", "rows": []}),
        )
        assert await HttpxGoogleMapsGateway("KEY").distancias_km((0.0, 0.0), [(1.0, 1.0)]) == []

    async def test_status_no_ok_y_errores_http_levantan(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gateway = HttpxGoogleMapsGateway("KEY")
        _inyectar(
            monkeypatch,
            httpx_google_maps_gateway,
            lambda r: httpx.Response(200, json={"status": "OVER_QUERY_LIMIT"}),
        )
        with pytest.raises(ExternalServiceError, match="OVER_QUERY_LIMIT"):
            await gateway.distancias_km((0.0, 0.0), [(1.0, 1.0)])

        _inyectar(monkeypatch, httpx_google_maps_gateway, lambda r: httpx.Response(403))
        with pytest.raises(ExternalServiceError, match="HTTP"):
            await gateway.distancias_km((0.0, 0.0), [(1.0, 1.0)])

        def caido(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        _inyectar(monkeypatch, httpx_google_maps_gateway, caido)
        with pytest.raises(ExternalServiceError, match="conexión"):
            await gateway.distancias_km((0.0, 0.0), [(1.0, 1.0)])
