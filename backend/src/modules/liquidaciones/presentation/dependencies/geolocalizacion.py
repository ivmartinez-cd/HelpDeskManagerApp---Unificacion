"""Factories de geolocalización a nivel prestador: estado del asistente,
cálculo de distancias, geocodificación de sucursales, coordenadas y pines
sospechosos.

Las factories del pipeline de geovalidación (Tier 0/1/1b/worklist) viven en
`geovalidacion.py` y las de acciones sobre filas de Tabla KM en
`tabla_km_geo.py` — separadas de este archivo porque juntas superaban el
tamaño máximo de archivo (§4).

Reusa el gateway pyodbc y el de Distance Matrix de `dependencies/siges.py`
(singletons de proceso); el de geocoding es otro singleton con la misma key.
El tope de llamadas viene de `GOOGLE_MAPS_MAX_CALLS_PER_RUN`."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    CalcularDistanciasPorts,
)
from src.modules.liquidaciones.application.use_cases.aplicar_calcular_distancias import (
    AplicarCalcularDistancias,
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
from src.modules.liquidaciones.application.use_cases.preview_calcular_distancias import (
    PreviewCalcularDistancias,
)
from src.modules.liquidaciones.application.use_cases.resolver_coordenadas import (
    CoordenadasPorts,
    ListarCoordenadasPendientes,
    ResolverCoordenadas,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_calculo_km_preview_repository import (  # noqa: E501
    SqlAlchemyCalculoKmPreviewRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_sucursal_coordenadas_repository import (  # noqa: E501
    SqlAlchemySucursalCoordenadasRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.presentation.dependencies.siges import (
    distancias_gateway,
    siges_catalogo_gateway,
    tope_llamadas_distancias,
)
from src.shared.infrastructure.geocoding.factories import (
    require_geocoding_gateway,
    tope_llamadas_geocoding,
)
from src.shared.infrastructure.geocoding.sqlalchemy_geocode_cache_repository import (  # noqa: E501
    SqlAlchemyGeocodeCacheRepository,
)


def _tope() -> int:
    """Tope del cálculo de distancias (proveedor de distancias)."""
    return tope_llamadas_distancias()


def _tope_geocoding() -> int:
    """Tope de geocodificación (proveedor de geocoding) — distinto del de
    distancias: con distancias en OSRM y geocoding en Google, el tope de Google
    tiene que seguir mandando sobre lo que se gasta."""
    return tope_llamadas_geocoding()


def _distancias_ports(session: AsyncSession) -> CalcularDistanciasPorts:
    return CalcularDistanciasPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        tabla_km=SqlAlchemyTablaKmRepository(session),
        siges=siges_catalogo_gateway(),
        google_maps=distancias_gateway(),
        sucursal_coords=SqlAlchemySucursalCoordenadasRepository(session),
        previews=SqlAlchemyCalculoKmPreviewRepository(session),
        incidentes=SqlAlchemyIncidenteRepository(session),
        spsts=SqlAlchemySpstRepository(session),
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
            geocoding=require_geocoding_gateway(),
            incidentes=SqlAlchemyIncidenteRepository(session),
        ),
        _tope_geocoding(),
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
        geocoding=require_geocoding_gateway(),
        sucursal_coords=SqlAlchemySucursalCoordenadasRepository(session),
    )


def build_listar_pines_sospechosos(session: AsyncSession) -> ListarPinesSospechosos:
    return ListarPinesSospechosos(_pines_ports(session))


def build_auditar_pines(session: AsyncSession) -> AuditarPines:
    return AuditarPines(_pines_ports(session), _tope_geocoding())


def build_corregir_pin(session: AsyncSession) -> CorregirPin:
    return CorregirPin(_pines_ports(session))


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
