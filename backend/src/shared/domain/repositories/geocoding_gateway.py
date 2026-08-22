"""Puerto de geocodificación de direcciones (Google Geocoding API) —
compartido entre módulos que necesitan resolver un domicilio a coordenadas
(liquidaciones, preventivos): la key es corporativa y paga, un solo puerto
evita duplicar el contrato con Google.

`location_type` y `tipos` vienen tal cual de Google: la elección automática de
candidato (ver `liquidaciones/domain/services/geolocalizacion.py`) los usa
para distinguir un match preciso (ROOFTOP / RANGE_INTERPOLATED / intersección)
de un centro geométrico de ruta — el muestreo de calidad 2026-08-15 mostró que
"Ruta X KM Y" devuelve el centro de toda la ruta, a kilómetros del punto
real."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeocodeCandidato:
    formatted_address: str
    latitud: float
    longitud: float
    location_type: str
    tipos: tuple[str, ...] = ()
    partial_match: bool = False


class GeocodingGateway(Protocol):
    async def geocode(self, direccion: str) -> list[GeocodeCandidato]:
        """Candidatos de Google para una dirección ya normalizada. Lista vacía
        cuando Google no encuentra nada (ZERO_RESULTS no es error)."""
        ...
