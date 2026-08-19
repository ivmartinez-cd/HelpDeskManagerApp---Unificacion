"""Puerto de la API Georef del Estado argentino (Tier 1 de geovalidación) —
gratuita, sin autenticación, sin rate limit publicado. Doc:
https://datosgobar.github.io/georef-ar-api/. Verificado en vivo 2026-08-19:
`/ubicacion` con `provincia.nombre == null` es "sin cobertura para ese punto"
(HTTP 200, no error)."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UbicacionGeoref:
    provincia_nombre: str
    provincia_id: str
    departamento_nombre: str | None
    departamento_id: str | None


class GeoreferenciacionGateway(Protocol):
    async def reverse(self, lat: float, lon: float) -> UbicacionGeoref | None:
        """`None` = sin cobertura para ese punto (Georef no tiene datos ahí,
        no es un error). Reintenta con backoff acotado ante 429/5xx; un error
        persistente se propaga como `ExternalServiceError` — no se reintenta
        en loop."""
        ...
