"""Factory compartida del gateway de geocodificación (mismo patrón que
`shared/infrastructure/mercurio/factories.py`, ADR-018): singleton de proceso,
un solo lugar que lee la config. Desde 2026-09-05 elige proveedor por
`GEOCODING_PROVEEDOR`: Google (key corporativa, paga) o Nominatim/OpenStreetMap
(gratis, 1 req/s). La settings sigue viviendo bajo `LiquidacionesSettings`
(fue el primer módulo en usarla) pero es config de toda la app."""

from functools import lru_cache

from src.shared.domain.errors import ExternalServiceError
from src.shared.domain.repositories.geocoding_gateway import GeocodingGateway
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.geocoding.httpx_geocoding_gateway import HttpxGeocodingGateway
from src.shared.infrastructure.geocoding.httpx_nominatim_geocoding_gateway import (
    HttpxNominatimGeocodingGateway,
)


@lru_cache
def require_geocoding_gateway() -> GeocodingGateway:
    settings = get_settings()
    if settings.geocoding_proveedor == "osm":
        return HttpxNominatimGeocodingGateway()
    if not settings.google_maps_api_key:
        raise ExternalServiceError(
            "Google Geocoding no está configurado — falta GOOGLE_MAPS_API_KEY"
        )
    return HttpxGeocodingGateway(settings.google_maps_api_key)


def tope_llamadas_geocoding() -> int:
    settings = get_settings()
    if settings.geocoding_proveedor == "osm":
        return settings.osm_geocoding_max_calls_per_run
    return settings.google_maps_max_calls_per_run
