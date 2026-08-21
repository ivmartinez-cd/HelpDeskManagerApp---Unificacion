"""Factories de las acciones de geolocalización sobre filas de Tabla KM
(búsqueda de lugar, refrescar direcciones desde Siges, recálculo) — separado
de `geolocalizacion.py` porque ese archivo ya superaba el tamaño máximo (§4).

Reusa el gateway pyodbc y el de Distance Matrix de `dependencies/siges.py`
(singletons de proceso)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.tabla_km_lugares import (
    BuscarLugarFila,
    RecalcularKmFila,
    ResolverCoordenadasFila,
    TablaKmLugaresPorts,
)
from src.modules.liquidaciones.application.use_cases.tabla_km_refrescar_siges import (
    RefrescarDatosSiges,
)
from src.modules.liquidaciones.infrastructure.google_maps.httpx_geocoding_gateway import (
    HttpxGeocodingGateway,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_geocode_cache_repository import (  # noqa: E501
    SqlAlchemyGeocodeCacheRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.presentation.dependencies.siges import (
    siges_catalogo_gateway,
    siges_google_maps_gateway,
)
from src.shared.infrastructure.config.settings import get_settings


@lru_cache
def _geocoding_gateway() -> HttpxGeocodingGateway:
    return HttpxGeocodingGateway(get_settings().google_maps_api_key)


def _lugares_ports(session: AsyncSession) -> TablaKmLugaresPorts:
    return TablaKmLugaresPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        tabla_km=SqlAlchemyTablaKmRepository(session),
        siges=siges_catalogo_gateway(),
        geocode_cache=SqlAlchemyGeocodeCacheRepository(session),
        geocoding=_geocoding_gateway(),
        google_maps=siges_google_maps_gateway(),
    )


def build_buscar_lugar_fila(session: AsyncSession) -> BuscarLugarFila:
    return BuscarLugarFila(_lugares_ports(session))


def build_refrescar_datos_siges(session: AsyncSession) -> RefrescarDatosSiges:
    return RefrescarDatosSiges(_lugares_ports(session))


def build_resolver_coordenadas_fila(session: AsyncSession) -> ResolverCoordenadasFila:
    return ResolverCoordenadasFila(_lugares_ports(session))


def build_recalcular_km_fila(session: AsyncSession) -> RecalcularKmFila:
    return RecalcularKmFila(_lugares_ports(session))
