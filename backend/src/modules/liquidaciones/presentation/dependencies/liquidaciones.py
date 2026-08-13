"""Factories de los casos de uso de liquidaciones — arman los repositorios
SQLAlchemy scoped a la sesión del request y los inyectan en el Ports del use case."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.get_liquidacion_detalle import (
    GetLiquidacionDetalle,
    GetLiquidacionDetallePorts,
)
from src.modules.liquidaciones.application.use_cases.importar_liquidacion import (
    ImportarLiquidacion,
    ImportarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.list_liquidaciones import (
    ListLiquidaciones,
    ListLiquidacionesPorts,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.infrastructure.importers.pandas_liquidacion_file_parser import (
    PandasLiquidacionFileParser,
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
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_observacion_repository import (  # noqa: E501
    SqlAlchemyObservacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_regla_alerta_repository import (  # noqa: E501
    SqlAlchemyReglaAlertaRepository,
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


def build_list_liquidaciones(session: AsyncSession) -> ListLiquidaciones:
    return ListLiquidaciones(
        ListLiquidacionesPorts(liquidaciones=SqlAlchemyLiquidacionRepository(session))
    )


def build_get_liquidacion_detalle(session: AsyncSession) -> GetLiquidacionDetalle:
    return GetLiquidacionDetalle(
        GetLiquidacionDetallePorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
            alertas=SqlAlchemyAlertaRepository(session),
            observaciones=SqlAlchemyObservacionRepository(session),
            tablas_km=SqlAlchemyTablaKmRepository(session),
        )
    )


def build_reanalizar_liquidacion(session: AsyncSession) -> ReanalizarLiquidacion:
    return ReanalizarLiquidacion(
        ReanalizarLiquidacionPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
            alertas=SqlAlchemyAlertaRepository(session),
            observaciones=SqlAlchemyObservacionRepository(session),
            reglas=SqlAlchemyReglaAlertaRepository(session),
            tablas_km=SqlAlchemyTablaKmRepository(session),
            spsts=SqlAlchemySpstRepository(session),
            tarifarios=SqlAlchemyTarifarioRepository(session),
        )
    )


def build_importar_liquidacion(session: AsyncSession) -> ImportarLiquidacion:
    return ImportarLiquidacion(
        ImportarLiquidacionPorts(
            parser=PandasLiquidacionFileParser(),
            prestadores=SqlAlchemyPrestadorRepository(session),
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
            reanalizar=build_reanalizar_liquidacion(session),
        )
    )
