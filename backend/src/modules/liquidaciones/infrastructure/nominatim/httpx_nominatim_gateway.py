"""Adapter httpx del puerto NominatimGateway — OpenStreetMap, gratuito.
Política de uso (https://operations.osmfoundation.org/policies/nominatim/):
máximo 1 req/s, User-Agent identificable propio (no el default de httpx),
secuencial. El rate limit se aplica acá con un lock de instancia — el
gateway es singleton de proceso, así que serializa TODAS las llamadas."""

import asyncio
import logging
import time
from typing import Any

import httpx

from src.modules.liquidaciones.domain.repositories.nominatim_gateway import UbicacionNominatim
from src.shared.domain.errors import ExternalServiceError

_LOG = logging.getLogger(__name__)
_BASE_URL = "https://nominatim.openstreetmap.org"
_USER_AGENT = "HelpDeskManager-CanalDirecto-Geovalidacion/1.0"
_TIMEOUT_SECONDS = 30.0
_MIN_INTERVALO_SEGUNDOS = 1.0


class HttpxNominatimGateway:
    def __init__(
        self,
        base_url: str = _BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url
        self._transport = transport
        self._lock = asyncio.Lock()
        self._ultima_llamada: float | None = None

    async def reverse(self, lat: float, lon: float) -> UbicacionNominatim | None:
        async with self._lock:
            await self._esperar_intervalo()
            data = await self._request(lat, lon)
            self._ultima_llamada = time.monotonic()
        if "error" in data:
            return None
        provincia = (data.get("address") or {}).get("state")
        return UbicacionNominatim(provincia_nombre=provincia) if provincia else None

    async def _esperar_intervalo(self) -> None:
        if self._ultima_llamada is None:
            return
        transcurrido = time.monotonic() - self._ultima_llamada
        if transcurrido < _MIN_INTERVALO_SEGUNDOS:
            await asyncio.sleep(_MIN_INTERVALO_SEGUNDOS - transcurrido)

    async def _request(self, lat: float, lon: float) -> dict[str, Any]:
        params: dict[str, str | float] = {"format": "jsonv2", "lat": lat, "lon": lon}
        headers = {"User-Agent": _USER_AGENT}
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT_SECONDS, transport=self._transport
            ) as client:
                resp = await client.get(f"{self._base_url}/reverse", params=params, headers=headers)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _LOG.error(
                "Nominatim HTTP error", extra={"status": exc.response.status_code}, exc_info=exc
            )
            raise ExternalServiceError("Error HTTP al llamar Nominatim") from exc
        except httpx.HTTPError as exc:
            _LOG.error("Nominatim connection error", exc_info=exc)
            raise ExternalServiceError("Error de conexión con Nominatim") from exc
        return resp.json()  # type: ignore[no-any-return]
