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
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.siges.pyodbc_siges_catalogo_gateway import (
    PyodbcSigesCatalogoGateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string


def _siges_ports(session: AsyncSession) -> SigesConfigPorts:
    settings = get_settings()
    gateway = PyodbcSigesCatalogoGateway(
        build_mercurio_connection_string(settings), settings.sla_mercurio_timeout_seconds
    )
    return SigesConfigPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        spsts=SqlAlchemySpstRepository(session),
        siges=gateway,
    )


def build_proponer_vinculos_siges(session: AsyncSession) -> ProponerVinculosSiges:
    return ProponerVinculosSiges(_siges_ports(session))


def build_vincular_prestador_siges(session: AsyncSession) -> VincularPrestadorSiges:
    return VincularPrestadorSiges(_siges_ports(session))


def build_vincular_spst_siges(session: AsyncSession) -> VincularSpstSiges:
    return VincularSpstSiges(_siges_ports(session))


def build_sync_config_desde_siges(session: AsyncSession) -> SyncConfigDesdeSiges:
    return SyncConfigDesdeSiges(_siges_ports(session))
