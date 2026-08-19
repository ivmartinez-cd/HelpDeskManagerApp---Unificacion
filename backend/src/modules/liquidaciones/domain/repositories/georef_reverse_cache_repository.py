"""Puerto del cache de reverse geocoding de Georef, por pin redondeado.

Georef es gratis pero no hay que abusar del servicio público: un pin ya
consultado no se vuelve a pedir. `ReverseCacheado.ubicacion is None` distingue
"consultado, sin cobertura" de "nunca consultado" (`get` devuelve `None`)."""

from dataclasses import dataclass
from typing import Protocol

from src.modules.liquidaciones.domain.repositories.georeferenciacion_gateway import (
    UbicacionGeoref,
)


@dataclass(frozen=True)
class ReverseCacheado:
    ubicacion: UbicacionGeoref | None


class GeorefReverseCacheRepository(Protocol):
    async def get(self, lat: float, lon: float) -> ReverseCacheado | None:
        """`None` = nunca consultado; `ReverseCacheado` = ya consultado."""
        ...

    async def put(self, lat: float, lon: float, ubicacion: UbicacionGeoref | None) -> None: ...
