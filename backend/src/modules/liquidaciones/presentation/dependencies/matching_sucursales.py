"""Factories de los casos de uso de matching de sucursales Tabla KM ↔ Siges
(Fase 1) — sin gateway de Google, es dominio+DB local+Siges read-only."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.matching_confirmar_rechazar_tabla_km import (
    ConfirmarRechazarPorts,
    ConfirmarVinculoTablaKm,
    RechazarPropuestaTablaKm,
)
from src.modules.liquidaciones.application.use_cases.matching_sucursales_tabla_km import (
    AutoVincularMatchesN1TablaKm,
    ListarPropuestasN2TablaKm,
    MatchingSucursalesPorts,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_matching_descarte_repository import (  # noqa: E501
    SqlAlchemyMatchingDescarteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.presentation.dependencies.siges import siges_catalogo_gateway


def _ports(session: AsyncSession) -> MatchingSucursalesPorts:
    return MatchingSucursalesPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        tabla_km=SqlAlchemyTablaKmRepository(session),
        siges=siges_catalogo_gateway(),
        descartes=SqlAlchemyMatchingDescarteRepository(session),
    )


def build_auto_vincular_n1(session: AsyncSession) -> AutoVincularMatchesN1TablaKm:
    return AutoVincularMatchesN1TablaKm(_ports(session))


def build_listar_propuestas_n2(session: AsyncSession) -> ListarPropuestasN2TablaKm:
    return ListarPropuestasN2TablaKm(_ports(session))


def _confirmar_rechazar_ports(session: AsyncSession) -> ConfirmarRechazarPorts:
    return ConfirmarRechazarPorts(
        prestadores=SqlAlchemyPrestadorRepository(session),
        tabla_km=SqlAlchemyTablaKmRepository(session),
        siges=siges_catalogo_gateway(),
        descartes=SqlAlchemyMatchingDescarteRepository(session),
    )


def build_confirmar_vinculo(session: AsyncSession) -> ConfirmarVinculoTablaKm:
    return ConfirmarVinculoTablaKm(_confirmar_rechazar_ports(session))


def build_rechazar_propuesta(session: AsyncSession) -> RechazarPropuestaTablaKm:
    return RechazarPropuestaTablaKm(SqlAlchemyMatchingDescarteRepository(session))
