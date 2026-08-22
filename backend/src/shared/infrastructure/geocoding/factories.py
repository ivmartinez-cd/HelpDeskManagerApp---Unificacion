"""Factory compartida del gateway de Google Geocoding (mismo patrón que
`shared/infrastructure/mercurio/factories.py`, ADR-018): singleton de
proceso, un solo lugar que lee la key. La settings sigue viviendo bajo
`LiquidacionesSettings` (fue el primer módulo en usarla, ver
`settings_groups.py`) pero es la config de Google Geocoding para toda la
app, no algo privado de liquidaciones — no se renombró para no tocar una
integración ya verificada en producción (mismo criterio que
`sla_mercurio_*`)."""

from functools import lru_cache

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.geocoding.httpx_geocoding_gateway import HttpxGeocodingGateway


@lru_cache
def require_geocoding_gateway() -> HttpxGeocodingGateway:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise ExternalServiceError(
            "Google Geocoding no está configurado — falta GOOGLE_MAPS_API_KEY"
        )
    return HttpxGeocodingGateway(settings.google_maps_api_key)
