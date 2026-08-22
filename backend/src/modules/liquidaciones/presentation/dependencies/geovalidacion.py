"""Factories del pipeline de geovalidación (Tier 0 → Tier 1 → Tier 1b →
worklist Tier 2), separado de `geolocalizacion.py` porque ese archivo ya
superaba el tamaño máximo (§4)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.geovalidacion_csv import (
    GenerarWorklistCsv,
    WorklistCsvPorts,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier0 import (
    EvaluarTier0Geovalidacion,
    GeovalidacionTier0Ports,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1 import (
    ConsultarGeorefReversePendientes,
    GeovalidacionTier1Ports,
    ListarHallazgosTier1,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1b import (
    ConsultarNominatimPendientes,
    GeovalidacionTier1bPorts,
    ListarHallazgosTier1b,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_worklist import (
    CalcularWorklistTier2,
    WorklistTier2Ports,
)
from src.modules.liquidaciones.infrastructure.georef.httpx_georef_gateway import (
    HttpxGeorefGateway,
)
from src.modules.liquidaciones.infrastructure.nominatim.httpx_nominatim_gateway import (
    HttpxNominatimGateway,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_georef_reverse_cache_repository import (  # noqa: E501
    SqlAlchemyGeorefReverseCacheRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_nominatim_reverse_cache_repository import (  # noqa: E501
    SqlAlchemyNominatimReverseCacheRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.presentation.dependencies.geolocalizacion import (
    build_listar_pines_sospechosos,
)
from src.modules.liquidaciones.presentation.dependencies.siges import siges_catalogo_gateway
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.geocoding.sqlalchemy_geocode_cache_repository import (  # noqa: E501
    SqlAlchemyGeocodeCacheRepository,
)


@lru_cache
def _georef_gateway() -> HttpxGeorefGateway:
    return HttpxGeorefGateway()


@lru_cache
def _nominatim_gateway() -> HttpxNominatimGateway:
    """Singleton de proceso — el rate limit de 1 req/s de Nominatim se aplica
    en la instancia (lock + timestamp), así que TIENE que ser la misma para
    todas las llamadas del proceso."""
    return HttpxNominatimGateway()


def build_evaluar_tier0(session: AsyncSession) -> EvaluarTier0Geovalidacion:
    """Sin gateways de red — Tier 0 es dominio puro sobre datos ya locales
    (Siges read-only), se puede recalcular en cada request sin costo."""
    return EvaluarTier0Geovalidacion(
        GeovalidacionTier0Ports(
            prestadores=SqlAlchemyPrestadorRepository(session),
            siges=siges_catalogo_gateway(),
        )
    )


def _tier1_ports(session: AsyncSession) -> GeovalidacionTier1Ports:
    return GeovalidacionTier1Ports(
        prestadores=SqlAlchemyPrestadorRepository(session),
        siges=siges_catalogo_gateway(),
        georef=_georef_gateway(),
        georef_cache=SqlAlchemyGeorefReverseCacheRepository(session),
    )


def build_consultar_georef_pendientes(session: AsyncSession) -> ConsultarGeorefReversePendientes:
    settings = get_settings()
    return ConsultarGeorefReversePendientes(
        _tier1_ports(session), settings.georef_max_calls_per_run, settings.georef_pausa_segundos
    )


def build_listar_hallazgos_tier1(session: AsyncSession) -> ListarHallazgosTier1:
    return ListarHallazgosTier1(_tier1_ports(session))


def _tier1b_ports(session: AsyncSession) -> GeovalidacionTier1bPorts:
    return GeovalidacionTier1bPorts(
        tier1=_tier1_ports(session),
        nominatim=_nominatim_gateway(),
        nominatim_cache=SqlAlchemyNominatimReverseCacheRepository(session),
    )


def build_consultar_nominatim_pendientes(session: AsyncSession) -> ConsultarNominatimPendientes:
    return ConsultarNominatimPendientes(
        _tier1b_ports(session), get_settings().nominatim_max_calls_per_run
    )


def build_listar_hallazgos_tier1b(session: AsyncSession) -> ListarHallazgosTier1b:
    return ListarHallazgosTier1b(_tier1b_ports(session))


def build_calcular_worklist_tier2(session: AsyncSession) -> CalcularWorklistTier2:
    return CalcularWorklistTier2(
        WorklistTier2Ports(
            prestadores=SqlAlchemyPrestadorRepository(session),
            siges=siges_catalogo_gateway(),
            geocode_cache=SqlAlchemyGeocodeCacheRepository(session),
            evaluar_tier0=build_evaluar_tier0(session),
            listar_tier1b=build_listar_hallazgos_tier1b(session),
        )
    )


def build_generar_worklist_csv(session: AsyncSession) -> GenerarWorklistCsv:
    return GenerarWorklistCsv(
        WorklistCsvPorts(
            calcular_worklist=build_calcular_worklist_tier2(session),
            listar_tier1b=build_listar_hallazgos_tier1b(session),
            listar_pines=build_listar_pines_sospechosos(session),
        )
    )
