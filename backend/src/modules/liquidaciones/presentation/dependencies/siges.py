"""Factories de los casos de uso de vínculo/sync contra Siges (ADR-014) — el
gateway pyodbc se arma desde la config de Mercurio ya existente (mismos settings
que sla/prestadores)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.siges_config import (
    ProponerVinculosSiges,
    SigesConfigPorts,
    SyncConfigDesdeSiges,
    VincularPrestadorSiges,
    VincularSpstSiges,
)
from src.modules.liquidaciones.application.use_cases.siges_sucursales import (
    BuscarSucursalesSiges,
    SigesSucursalesPorts,
)
from src.modules.liquidaciones.application.use_cases.siges_tarifarios import (
    EstadoZonasSiges,
    MapearZonaSiges,
    SigesTarifariosPorts,
    SyncTarifariosDesdeSiges,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (  # noqa: E501
    SqlAlchemyTarifarioRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_zona_map_repository import (  # noqa: E501
    SqlAlchemyTarifarioZonaMapRepository,
)
from src.modules.liquidaciones.infrastructure.siges.pyodbc_siges_catalogo_gateway import (
    PyodbcSigesCatalogoGateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string


def _gateway() -> PyodbcSigesCatalogoGateway:
    settings = get_settings()
    return PyodbcSigesCatalogoGateway(
        build_mercurio_connection_string(settings), settings.sla_mercurio_timeout_seconds
    )


def _siges_ports(session: AsyncSession) -> SigesConfigPorts:
    return SigesConfigPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        spsts=SqlAlchemySpstRepository(session),
        siges=_gateway(),
    )


def build_proponer_vinculos_siges(session: AsyncSession) -> ProponerVinculosSiges:
    return ProponerVinculosSiges(_siges_ports(session))


def build_vincular_prestador_siges(session: AsyncSession) -> VincularPrestadorSiges:
    return VincularPrestadorSiges(_siges_ports(session))


def build_vincular_spst_siges(session: AsyncSession) -> VincularSpstSiges:
    return VincularSpstSiges(_siges_ports(session))


def build_sync_config_desde_siges(session: AsyncSession) -> SyncConfigDesdeSiges:
    return SyncConfigDesdeSiges(_siges_ports(session))


def _siges_tarifarios_ports(session: AsyncSession) -> SigesTarifariosPorts:
    return SigesTarifariosPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        tarifarios=SqlAlchemyTarifarioRepository(session),
        zona_maps=SqlAlchemyTarifarioZonaMapRepository(session),
        siges=_gateway(),
    )


def build_estado_zonas_siges(session: AsyncSession) -> EstadoZonasSiges:
    return EstadoZonasSiges(_siges_tarifarios_ports(session))


def build_mapear_zona_siges(session: AsyncSession) -> MapearZonaSiges:
    return MapearZonaSiges(_siges_tarifarios_ports(session))


def build_sync_tarifarios_desde_siges(session: AsyncSession) -> SyncTarifariosDesdeSiges:
    return SyncTarifariosDesdeSiges(_siges_tarifarios_ports(session))


def build_buscar_sucursales_siges(session: AsyncSession) -> BuscarSucursalesSiges:
    return BuscarSucursalesSiges(
        SigesSucursalesPorts(
            prestadores=SqlAlchemyPrestadorRepository(session),
            tabla_km=SqlAlchemyTablaKmRepository(session),
            siges=_gateway(),
        )
    )
