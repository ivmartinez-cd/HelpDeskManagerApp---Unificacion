"""Adapter httpx del puerto GeocodingGateway — Google Geocoding API.

Sin retries a propósito (misma política que el gateway de Distance Matrix de
liquidaciones): la key es paga y un error se reporta, no se reintenta en
silencio."""

import logging
from typing import Any

import httpx

from src.shared.domain.errors import ExternalServiceError
from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato

_LOG = logging.getLogger(__name__)
_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


class HttpxGeocodingGateway:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def geocode(self, direccion: str) -> list[GeocodeCandidato]:
        data = await self._http_get(direccion)
        status = data.get("status")
        if status == "ZERO_RESULTS":
            return []
        if status != "OK":
            _LOG.error(
                "Google Geocoding status not OK",
                extra={"status": status, "error_message": data.get("error_message")},
            )
            raise ExternalServiceError(f"Google Geocoding: {status}")
        return [_parse_result(r) for r in data.get("results", [])]

    async def _http_get(self, direccion: str) -> dict[str, Any]:
        params = {"address": direccion, "key": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(_GEOCODE_URL, params=params)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _LOG.error(
                "Google Geocoding HTTP error",
                extra={"status": exc.response.status_code},
                exc_info=exc,
            )
            raise ExternalServiceError("Error HTTP al llamar Google Geocoding") from exc
        except httpx.HTTPError as exc:
            _LOG.error("Google Geocoding connection error", exc_info=exc)
            raise ExternalServiceError("Error de conexión con Google Geocoding") from exc
        return resp.json()  # type: ignore[no-any-return]


def _parse_result(result: dict[str, Any]) -> GeocodeCandidato:
    geometry = result.get("geometry", {})
    location = geometry.get("location", {})
    return GeocodeCandidato(
        formatted_address=result.get("formatted_address", ""),
        latitud=float(location.get("lat", 0.0)),
        longitud=float(location.get("lng", 0.0)),
        location_type=geometry.get("location_type", ""),
        tipos=tuple(result.get("types", [])),
        partial_match=bool(result.get("partial_match", False)),
    )
