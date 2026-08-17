"""Factories de los casos de uso de geolocalización y cálculo de distancias.

Reusa el gateway pyodbc y el de Distance Matrix de `dependencies/siges.py`
(singletons de proceso); el de geocoding es otro singleton con la misma key.
El tope de llamadas viene de `GOOGLE_MAPS_MAX_CALLS_PER_RUN`."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.calcular_distancias_siges import (
    AplicarCalcularDistancias,
    CalcularDistanciasPorts,
    PreviewCalcularDistancias,
)
from src.modules.liquidaciones.application.use_cases.estado_asistente_km import (
    DiagnosticarAsistenteKm,
    EstadoAsistenteKmPorts,
)
from src.modules.liquidaciones.application.use_cases.geocodificar_sucursales import (
    GeocodificarPorts,
    GeocodificarSucursales,
)
from src.modules.liquidaciones.application.use_cases.pines_sospechosos import (
    AuditarPines,
    CorregirPin,
    ListarPinesSospechosos,
    PinesPorts,
)
from src.modules.liquidaciones.application.use_cases.resolver_coordenadas import (
    CoordenadasPorts,
    ListarCoordenadasPendientes,
    ResolverCoordenadas,
)
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
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_calculo_km_preview_repository import (  # noqa: E501
    SqlAlchemyCalculoKmPreviewRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_geocode_cache_repository import (  # noqa: E501
    SqlAlchemyGeocodeCacheRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_sucursal_coordenadas_repository import (  # noqa: E501
    SqlAlchemySucursalCoordenadasRepository,
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


def _tope() -> int:
    return get_settings().google_maps_max_calls_per_run


def _distancias_ports(session: AsyncSession) -> CalcularDistanciasPorts:
    return CalcularDistanciasPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        tabla_km=SqlAlchemyTablaKmRepository(session),
        siges=siges_catalogo_gateway(),
        google_maps=siges_google_maps_gateway(),
        sucursal_coords=SqlAlchemySucursalCoordenadasRepository(session),
        previews=SqlAlchemyCalculoKmPreviewRepository(session),
        incidentes=SqlAlchemyIncidenteRepository(session),
    )


def build_preview_calcular_distancias(session: AsyncSession) -> PreviewCalcularDistancias:
    return PreviewCalcularDistancias(_distancias_ports(session), _tope())


def build_aplicar_calcular_distancias(session: AsyncSession) -> AplicarCalcularDistancias:
    return AplicarCalcularDistancias(_distancias_ports(session))


def build_geocodificar_sucursales(session: AsyncSession) -> GeocodificarSucursales:
    return GeocodificarSucursales(
        GeocodificarPorts(
            prestadores=SqlAlchemyPrestadorRepository(session),
            siges=siges_catalogo_gateway(),
            sucursal_coords=SqlAlchemySucursalCoordenadasRepository(session),
            geocode_cache=SqlAlchemyGeocodeCacheRepository(session),
            geocoding=_geocoding_gateway(),
            incidentes=SqlAlchemyIncidenteRepository(session),
        ),
        _tope(),
    )


def _coordenadas_ports(session: AsyncSession) -> CoordenadasPorts:
    return CoordenadasPorts(
        sucursal_coords=SqlAlchemySucursalCoordenadasRepository(session),
        geocode_cache=SqlAlchemyGeocodeCacheRepository(session),
    )


def build_listar_coordenadas_pendientes(session: AsyncSession) -> ListarCoordenadasPendientes:
    return ListarCoordenadasPendientes(_coordenadas_ports(session))


def build_resolver_coordenadas(session: AsyncSession) -> ResolverCoordenadas:
    return ResolverCoordenadas(_coordenadas_ports(session))


def _pines_ports(session: AsyncSession) -> PinesPorts:
    return PinesPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        siges=siges_catalogo_gateway(),
        geocode_cache=SqlAlchemyGeocodeCacheRepository(session),
        geocoding=_geocoding_gateway(),
        sucursal_coords=SqlAlchemySucursalCoordenadasRepository(session),
    )


def build_listar_pines_sospechosos(session: AsyncSession) -> ListarPinesSospechosos:
    return ListarPinesSospechosos(_pines_ports(session))


def build_auditar_pines(session: AsyncSession) -> AuditarPines:
    return AuditarPines(_pines_ports(session), _tope())


def build_corregir_pin(session: AsyncSession) -> CorregirPin:
    return CorregirPin(_pines_ports(session))


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


def build_diagnosticar_asistente_km(session: AsyncSession) -> DiagnosticarAsistenteKm:
    """Sin gateway de geocoding a propósito: el diagnóstico no puede gastar
    Google ni por accidente — la garantía es estructural."""
    return DiagnosticarAsistenteKm(
        EstadoAsistenteKmPorts(
            prestadores=SqlAlchemyPrestadorRepository(session),
            siges=siges_catalogo_gateway(),
            tabla_km=SqlAlchemyTablaKmRepository(session),
            sucursal_coords=SqlAlchemySucursalCoordenadasRepository(session),
            geocode_cache=SqlAlchemyGeocodeCacheRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
        ),
        _tope(),
    )
