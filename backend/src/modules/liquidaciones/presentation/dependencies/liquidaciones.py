"""Factories de los casos de uso de liquidaciones — arman los repositorios
SQLAlchemy scoped a la sesión del request y los inyectan en el Ports del use case.

El gateway wsAyC es singleton de proceso (`lru_cache`), igual que el de
insumos (ADR-018) — antes se instanciaba uno nuevo por request y cada uno
re-descargaba y re-parseaba el WSDL en su primera llamada (~0,31 s medidos)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacion,
    ReconciliarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.actualizar_estado_alerta import (
    ActualizarEstadoAlerta,
    ActualizarEstadoAlertaPorts,
)
from src.modules.liquidaciones.application.use_cases.actualizar_estado_alertas_lote import (
    ActualizarEstadoAlertasLote,
)
from src.modules.liquidaciones.application.use_cases.actualizar_estado_local import (
    ActualizarEstadoLocal,
    ActualizarEstadoLocalPorts,
)
from src.modules.liquidaciones.application.use_cases.actualizar_extra_liquidacion import (
    ActualizarExtraLiquidacion,
    ActualizarExtraLiquidacionPorts,
)
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
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reconciliar_liquidacion_individual import (
    ReconciliarLiquidacionIndividual,
    ReconciliarLiquidacionIndividualPorts,
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
from src.modules.liquidaciones.presentation.dependencies.notificaciones import (
    build_notificador,
)
from src.shared.infrastructure.database.engine import get_engine
from src.shared.infrastructure.locks.postgres_advisory_lock import (
    LIQUIDACIONES_SINCRONIZAR_LOCK_KEY,
    PostgresAdvisoryLock,
)


@lru_cache
def cd_gateway() -> ZeepCdLiquidacionesGateway:
    return ZeepCdLiquidacionesGateway()


@lru_cache
def _sync_lock() -> PostgresAdvisoryLock:
    return PostgresAdvisoryLock(get_engine(), LIQUIDACIONES_SINCRONIZAR_LOCK_KEY)


def build_list_liquidaciones(session: AsyncSession) -> ListLiquidaciones:
    return ListLiquidaciones(
        ListLiquidacionesPorts(liquidaciones=SqlAlchemyLiquidacionRepository(session))
    )


def build_actualizar_estado_local(session: AsyncSession) -> ActualizarEstadoLocal:
    return ActualizarEstadoLocal(
        ActualizarEstadoLocalPorts(liquidaciones=SqlAlchemyLiquidacionRepository(session))
    )


def build_actualizar_extra_liquidacion(session: AsyncSession) -> ActualizarExtraLiquidacion:
    return ActualizarExtraLiquidacion(
        ActualizarExtraLiquidacionPorts(liquidaciones=SqlAlchemyLiquidacionRepository(session))
    )


def build_actualizar_estado_alerta(session: AsyncSession) -> ActualizarEstadoAlerta:
    return ActualizarEstadoAlerta(
        ActualizarEstadoAlertaPorts(
            alertas=SqlAlchemyAlertaRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
        )
    )


def build_actualizar_estado_alertas_lote(session: AsyncSession) -> ActualizarEstadoAlertasLote:
    return ActualizarEstadoAlertasLote(
        ActualizarEstadoAlertaPorts(
            alertas=SqlAlchemyAlertaRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
        )
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


def build_reconciliar_liquidacion(session: AsyncSession) -> ReconciliarLiquidacion:
    return ReconciliarLiquidacion(
        ReconciliarLiquidacionPorts(
            incidentes=SqlAlchemyIncidenteRepository(session),
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            reanalizar=build_reanalizar_liquidacion(session),
            cd_gateway=cd_gateway(),
        )
    )


def build_reconciliar_liquidacion_individual(
    session: AsyncSession,
) -> ReconciliarLiquidacionIndividual:
    return ReconciliarLiquidacionIndividual(
        ReconciliarLiquidacionIndividualPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            prestadores=SqlAlchemyPrestadorRepository(session),
            cd_gateway=cd_gateway(),
            reconciliar=build_reconciliar_liquidacion(session),
        )
    )


def build_sincronizar_liquidaciones(session: AsyncSession) -> SincronizarLiquidaciones:
    return SincronizarLiquidaciones(
        SincronizarLiquidacionesPorts(
            cd_gateway=cd_gateway(),
            prestadores=SqlAlchemyPrestadorRepository(session),
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            incidentes=SqlAlchemyIncidenteRepository(session),
            reanalizar=build_reanalizar_liquidacion(session),
            reconciliar=build_reconciliar_liquidacion(session),
            sync_lock=_sync_lock(),
        )
    )


def build_aprobar_liquidacion(session: AsyncSession) -> AprobarLiquidacion:
    return AprobarLiquidacion(
        AprobarLiquidacionPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            cd_gateway=cd_gateway(),
            notificador=build_notificador(),
        )
    )


def build_anular_liquidacion(session: AsyncSession) -> AnularLiquidacion:
    return AnularLiquidacion(
        AnularLiquidacionPorts(
            liquidaciones=SqlAlchemyLiquidacionRepository(session),
            cd_gateway=cd_gateway(),
        )
    )


def build_backfill_estado(session: AsyncSession) -> BackfillEstadoLiquidaciones:
    return BackfillEstadoLiquidaciones(
        BackfillEstadoLiquidacionesPorts(
            cd_gateway=cd_gateway(),
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
