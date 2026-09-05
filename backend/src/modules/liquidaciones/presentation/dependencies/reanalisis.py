"""Builders del reanálisis (motor de reglas): por liquidación y para todas las
abiertas de un prestador — separados de `liquidaciones.py` por el límite de
tamaño de archivo (§4)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidaciones_abiertas import (  # noqa: E501
    ReanalizarLiquidacionesAbiertas,
    ReanalizarLiquidacionesAbiertasPorts,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_acuerdo_precio_cliente_repository import (  # noqa: E501
    SqlAlchemyAcuerdoPrecioClienteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_regla_alerta_repository import (  # noqa: E501
    SqlAlchemyReglaAlertaRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (  # noqa: E501
    SqlAlchemyTarifarioRepository,
)


def build_reanalizar_liquidacion(session: AsyncSession) -> ReanalizarLiquidacion:
    return ReanalizarLiquidacion(
        ReanalizarLiquidacionPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
            alertas=SqlAlchemyAlertaRepository(session),
            reglas=SqlAlchemyReglaAlertaRepository(session),
            tablas_km=SqlAlchemyTablaKmRepository(session),
            tarifarios=SqlAlchemyTarifarioRepository(session),
            acuerdos=SqlAlchemyAcuerdoPrecioClienteRepository(session),
        )
    )


def build_reanalizar_liquidaciones_abiertas(
    session: AsyncSession,
) -> ReanalizarLiquidacionesAbiertas:
    return ReanalizarLiquidacionesAbiertas(
        ReanalizarLiquidacionesAbiertasPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            reanalizar=build_reanalizar_liquidacion(session),
        )
    )
