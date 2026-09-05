"""Adapter httpx del puerto GeocodingGateway sobre Nominatim (OpenStreetMap) —
alternativa gratuita a Google Geocoding (decisión del usuario 2026-09-05:
arreglar las direcciones de Tabla KM sin depender de la key paga).

Política de uso de Nominatim: máximo 1 req/s, User-Agent propio, resultados
cacheados (lo hace `GeocodeCacheRepository`, igual que con Google). Mapeo al
vocabulario de Google que ya usa `elegir_automatico`:
- `location_type`: ROOFTOP si el resultado tiene altura (house_number) o es un
  punto de interés (amenity/shop/office/building); GEOMETRIC_CENTER + tipo
  `route` si es una calle/ruta entera; APPROXIMATE para localidades/áreas.
- `partial_match`: la consulta traía altura y el resultado no.
`tipos` lleva `(class, type, addresstype)` de OSM para que el humano vea qué
encontró (en la bandeja de revisión)."""

import asyncio
import logging
import re
import time
from typing import Any

import httpx

from src.shared.domain.errors import ExternalServiceError
from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato

_LOG = logging.getLogger(__name__)
_BASE_URL = "https://nominatim.openstreetmap.org"
_USER_AGENT = "HelpDeskManager-CanalDirecto-Geocoding/1.0"
_TIMEOUT_SECONDS = 30.0
_MIN_INTERVALO_SEGUNDOS = 1.0
_MAX_CANDIDATOS = 5
_CON_ALTURA = re.compile(r"\b\d{1,5}\b")
_CLASES_POI = frozenset({"amenity", "shop", "office", "building", "aeroway", "industrial"})
_AREAS = frozenset({"city", "town", "village", "hamlet", "suburb", "state", "county", "postcode"})


class HttpxNominatimGeocodingGateway:
    def __init__(self, base_url: str = _BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")
        self._lock = asyncio.Lock()
        self._ultima_llamada: float | None = None

    async def geocode(self, direccion: str) -> list[GeocodeCandidato]:
        async with self._lock:
            await self._esperar_intervalo()
            data = await self._request(direccion)
            self._ultima_llamada = time.monotonic()
        pide_altura = bool(_CON_ALTURA.search(direccion.split(",")[0]))
        return [_a_candidato(r, pide_altura) for r in data[:_MAX_CANDIDATOS]]

    async def _esperar_intervalo(self) -> None:
        if self._ultima_llamada is None:
            return
        transcurrido = time.monotonic() - self._ultima_llamada
        if transcurrido < _MIN_INTERVALO_SEGUNDOS:
            await asyncio.sleep(_MIN_INTERVALO_SEGUNDOS - transcurrido)

    async def _request(self, direccion: str) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                resp = await client.get(
                    f"{self._base_url}/search",
                    params=_params(direccion),
                    headers={"User-Agent": _USER_AGENT},
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _LOG.error("Nominatim search HTTP %s", exc.response.status_code, exc_info=exc)
            raise ExternalServiceError("Error HTTP al llamar Nominatim (OpenStreetMap)") from exc
        except httpx.HTTPError as exc:
            _LOG.error("Nominatim search connection error", exc_info=exc)
            raise ExternalServiceError("Error de conexión con Nominatim (OpenStreetMap)") from exc
        data = resp.json()
        return data if isinstance(data, list) else []


def _params(direccion: str) -> dict[str, str]:
    return {
        "q": direccion,
        "format": "jsonv2",
        "addressdetails": "1",
        "limit": str(_MAX_CANDIDATOS),
        "countrycodes": "ar",
    }


def _a_candidato(r: dict[str, Any], pide_altura: bool) -> GeocodeCandidato:
    address = r.get("address") or {}
    clase, tipo, addresstype = r.get("class", ""), r.get("type", ""), r.get("addresstype", "")
    tiene_altura = "house_number" in address
    return GeocodeCandidato(
        formatted_address=str(r.get("display_name", "")),
        latitud=float(r["lat"]),
        longitud=float(r["lon"]),
        location_type=_location_type(clase, addresstype, tiene_altura),
        tipos=tuple(t for t in (clase, tipo, addresstype) if t),
        partial_match=pide_altura and not tiene_altura,
    )


def _location_type(clase: str, addresstype: str, tiene_altura: bool) -> str:
    if clase == "highway":
        return "GEOMETRIC_CENTER"
    if tiene_altura or clase in _CLASES_POI:
        return "ROOFTOP"
    if addresstype in _AREAS or clase in ("place", "boundary"):
        return "APPROXIMATE"
    return "GEOMETRIC_CENTER"
