"""Factories de los casos de uso de liquidaciones — arman los repositorios
SQLAlchemy scoped a la sesión del request y los inyectan en el Ports del use case.

El gateway wsAyC es singleton de proceso (`lru_cache`), igual que el de
insumos (ADR-018) — antes se instanciaba uno nuevo por request y cada uno
re-descargaba y re-parseaba el WSDL en su primera llamada (~0,31 s medidos)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.anular_liquidacion import (
    AnularLiquidacion,
    AnularLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.aprobar_liquidacion import (
    AprobarLiquidacion,
    AprobarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.backfill_estado_liquidaciones import (
    BackfillEstadoLiquidaciones,
    BackfillEstadoLiquidacionesPorts,
)
from src.modules.liquidaciones.application.use_cases.get_liquidacion_detalle import (
    GetLiquidacionDetalle,
    GetLiquidacionDetallePorts,
)
from src.modules.liquidaciones.application.use_cases.importar_liquidacion import (
    ImportarLiquidacion,
    ImportarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.importar_prestador_maestro import (
    ImportarPrestadorMaestro,
    ImportarPrestadorMaestroPorts,
)
from src.modules.liquidaciones.application.use_cases.list_liquidaciones import (
    ListLiquidaciones,
    ListLiquidacionesPorts,
)
from src.modules.liquidaciones.application.use_cases.observar_liquidacion import (
    ObservarLiquidacion,
    ObservarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.sincronizar_liquidaciones import (
    SincronizarLiquidaciones,
    SincronizarLiquidacionesPorts,
)
from src.modules.liquidaciones.infrastructure.importers.pandas_liquidacion_file_parser import (
    PandasLiquidacionFileParser,
)
from src.modules.liquidaciones.infrastructure.importers.pandas_prestador_maestro_file_parser import (  # noqa: E501
    PandasPrestadorMaestroFileParser,
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
from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)


@lru_cache
def _cd_gateway() -> ZeepCdLiquidacionesGateway:
    return ZeepCdLiquidacionesGateway()


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


def build_sincronizar_liquidaciones(session: AsyncSession) -> SincronizarLiquidaciones:
    return SincronizarLiquidaciones(
        SincronizarLiquidacionesPorts(
            cd_gateway=_cd_gateway(),
            prestadores=SqlAlchemyPrestadorRepository(session),
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
            reanalizar=build_reanalizar_liquidacion(session),
        )
    )


def build_aprobar_liquidacion(session: AsyncSession) -> AprobarLiquidacion:
    return AprobarLiquidacion(
        AprobarLiquidacionPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            cd_gateway=_cd_gateway(),
        )
    )


def build_observar_liquidacion(session: AsyncSession) -> ObservarLiquidacion:
    return ObservarLiquidacion(
        ObservarLiquidacionPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            cd_gateway=_cd_gateway(),
        )
    )


def build_anular_liquidacion(session: AsyncSession) -> AnularLiquidacion:
    return AnularLiquidacion(
        AnularLiquidacionPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            cd_gateway=_cd_gateway(),
        )
    )


def build_backfill_estado(session: AsyncSession) -> BackfillEstadoLiquidaciones:
    return BackfillEstadoLiquidaciones(
        BackfillEstadoLiquidacionesPorts(
            cd_gateway=_cd_gateway(),
            prestadores=SqlAlchemyPrestadorRepository(session),
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
        )
    )


def build_importar_prestador_maestro(session: AsyncSession) -> ImportarPrestadorMaestro:
    return ImportarPrestadorMaestro(
        ImportarPrestadorMaestroPorts(
            parser=PandasPrestadorMaestroFileParser(),
            prestadores=SqlAlchemyPrestadorRepository(session),
            spsts=SqlAlchemySpstRepository(session),
            tarifarios=SqlAlchemyTarifarioRepository(session),
            tabla_km=SqlAlchemyTablaKmRepository(session),
        )
    )
