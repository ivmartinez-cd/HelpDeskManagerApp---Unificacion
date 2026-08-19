"""Puerto de Nominatim (OpenStreetMap) — segunda opinión de reverse geocoding,
SOLO para pines donde Georef ya marcó incompatibilidad o no tiene cobertura
(Tier 1b, nunca corre sobre el universo completo). Doc de política de uso:
https://operations.osmfoundation.org/policies/nominatim/. Verificado en vivo
2026-08-19: `{"error": "Unable to geocode"}` con HTTP 200 es "sin resultado"."""

from dataclasses import dataclass
from typing import Protocol

ATRIBUCION_ODBL = "Data © OpenStreetMap contributors, ODbL 1.0 — http://osm.org/copyright"


@dataclass(frozen=True)
class UbicacionNominatim:
    provincia_nombre: str


class NominatimGateway(Protocol):
    async def reverse(self, lat: float, lon: float) -> UbicacionNominatim | None:
        """`None` = sin resultado. El adapter real aplica el rate limit de
        1 req/s de la política de Nominatim — este puerto no lo modela, es
        responsabilidad del adapter."""
        ...
