"""Factories de los casos de uso que propagan estado a wsAyC (observar/recibir)
— separados de `liquidaciones.py`, que está al límite de tamaño (§4)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.observar_liquidacion import (
    ObservarLiquidacion,
)
from src.modules.liquidaciones.application.use_cases.propagar_estado_ayc import (
    PropagarEstadoAyCPorts,
)
from src.modules.liquidaciones.application.use_cases.recibir_liquidacion import (
    RecibirLiquidacion,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.presentation.dependencies.liquidaciones import cd_gateway


def _ports(session: AsyncSession) -> PropagarEstadoAyCPorts:
    return PropagarEstadoAyCPorts(
        liquidaciones=SqlAlchemyLiquidacionRepository(session),
        cd_gateway=cd_gateway(),
    )


def build_observar_liquidacion(session: AsyncSession) -> ObservarLiquidacion:
    return ObservarLiquidacion(_ports(session))


def build_recibir_liquidacion(session: AsyncSession) -> RecibirLiquidacion:
    return RecibirLiquidacion(_ports(session))
