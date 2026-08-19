"""Puerto del cache de reverse geocoding de Nominatim — cache obligatoria por
la política de uso del servicio (no solo cortesía como con Georef)."""

from dataclasses import dataclass
from typing import Protocol

from src.modules.liquidaciones.domain.repositories.nominatim_gateway import UbicacionNominatim


@dataclass(frozen=True)
class NominatimCacheado:
    ubicacion: UbicacionNominatim | None


class NominatimReverseCacheRepository(Protocol):
    async def get(self, lat: float, lon: float) -> NominatimCacheado | None:
        """`None` = nunca consultado."""
        ...

    async def put(self, lat: float, lon: float, ubicacion: UbicacionNominatim | None) -> None: ...
