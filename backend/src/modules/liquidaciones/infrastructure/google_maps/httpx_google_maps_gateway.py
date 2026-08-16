"""Adapter httpx del puerto GoogleMapsGateway — Distance Matrix API."""

import logging
from typing import Any

import httpx

from src.modules.liquidaciones.domain.repositories.google_maps_gateway import IdaVuelta
from src.shared.domain.errors import ExternalServiceError

_LOG = logging.getLogger(__name__)
_DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


def _coords_str(puntos: list[tuple[float, float]]) -> str:
    return "|".join(f"{lat},{lon}" for lat, lon in puntos)


class HttpxGoogleMapsGateway:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def distancias_km(
        self,
        origin: tuple[float, float],
        destinations: list[tuple[float, float]],
    ) -> list[float | None]:
        if not destinations:
            return []
        data = await self._call_api([origin], destinations)
        return _parse_elements(data)

    async def distancias_km_ida_vuelta(
        self,
        base: tuple[float, float],
        destinos: list[tuple[float, float]],
    ) -> list[IdaVuelta]:
        """Dos requests por lote: base→destinos (una fila de N elementos) y
        destinos→base (N filas de 1 elemento) — la vuelta es el tramo real B→A."""
        if not destinos:
            return []
        idas = _parse_elements(await self._call_api([base], destinos))
        data_vuelta = await self._call_api(destinos, [base])
        vueltas = [_parse_primer_elemento(row) for row in data_vuelta.get("rows", [])]
        return list(zip(idas, vueltas, strict=True))

    async def _call_api(
        self,
        origins: list[tuple[float, float]],
        destinations: list[tuple[float, float]],
    ) -> dict[str, Any]:
        data = await self._http_get(_coords_str(origins), _coords_str(destinations))
        if data.get("status") != "OK":
            _LOG.error(
                "Google Maps Distance Matrix status not OK",
                extra={"status": data.get("status"), "error_message": data.get("error_message")},
            )
            raise ExternalServiceError(f"Google Maps Distance Matrix: {data.get('status')}")
        return data

    async def _http_get(self, origins_str: str, dests_str: str) -> dict[str, Any]:
        params = {
            "origins": origins_str,
            "destinations": dests_str,
            "mode": "driving",
            "units": "metric",
            "key": self._api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(_DISTANCE_MATRIX_URL, params=params)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _LOG.error(
                "Google Maps HTTP error",
                extra={"status": exc.response.status_code},
                exc_info=exc,
            )
            raise ExternalServiceError("Error HTTP al llamar Google Maps Distance Matrix") from exc
        except httpx.HTTPError as exc:
            _LOG.error("Google Maps connection error", exc_info=exc)
            raise ExternalServiceError("Error de conexión con Google Maps") from exc
        return resp.json()  # type: ignore[no-any-return]


def _parse_elements(data: dict[str, Any]) -> list[float | None]:
    results: list[float | None] = []
    rows: list[Any] = data.get("rows", [])
    if not rows:
        return results
    for element in rows[0].get("elements", []):
        results.append(_km_de_elemento(element))
    return results


def _parse_primer_elemento(row: dict[str, Any]) -> float | None:
    elements = row.get("elements", [])
    return _km_de_elemento(elements[0]) if elements else None


def _km_de_elemento(element: dict[str, Any]) -> float | None:
    if element.get("status") != "OK":
        return None
    return float(element["distance"]["value"]) / 1000.0
