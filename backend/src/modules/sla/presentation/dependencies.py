"""Factories del módulo sla — gateways y use cases. Singletons de proceso
(`lru_cache`) como los gateways de insumos. El chequeo de host y el runner con
su semáforo viven en `require_mercurio_runner` (ADR-018)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sla.application.use_cases.get_pendientes_resumen import GetPendientesResumen
from src.modules.sla.application.use_cases.get_sla_compliance import GetSlaCompliance
from src.modules.sla.application.use_cases.list_incidentes_vencidos import (
    ListIncidentesVencidos,
)
from src.modules.sla.application.use_cases.list_pendientes import ListPendientes
from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.infrastructure.mercurio.pyodbc_pendientes_query_gateway import (
    PyodbcPendientesQueryGateway,
)
from src.modules.sla.infrastructure.mercurio.pyodbc_sla_query_gateway import (
    PyodbcSlaQueryGateway,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_pendientes_snapshot_repository import (
    SqlAlchemyPendientesSnapshotRepository,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_prestador_lookup import (
    SqlAlchemyPrestadorLookup,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_sla_snapshot_repository import (
    SqlAlchemySlaSnapshotRepository,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner


@lru_cache
def get_sla_query_gateway() -> PyodbcSlaQueryGateway:
    return PyodbcSlaQueryGateway(require_mercurio_runner())


@lru_cache
def get_pendientes_query_gateway() -> PyodbcPendientesQueryGateway:
    return PyodbcPendientesQueryGateway(require_mercurio_runner())


def build_refresh_sla_snapshot(session: AsyncSession) -> RefreshSlaSnapshot:
    return RefreshSlaSnapshot(get_sla_query_gateway(), SqlAlchemySlaSnapshotRepository(session))


def build_get_sla_compliance(session: AsyncSession) -> GetSlaCompliance:
    return GetSlaCompliance(
        SqlAlchemySlaSnapshotRepository(session), build_refresh_sla_snapshot(session)
    )


def build_list_incidentes_vencidos(session: AsyncSession) -> ListIncidentesVencidos:
    return ListIncidentesVencidos(
        SqlAlchemySlaSnapshotRepository(session), build_refresh_sla_snapshot(session)
    )


def build_refresh_pendientes_snapshot(session: AsyncSession) -> RefreshPendientesSnapshot:
    settings = get_settings()
    return RefreshPendientesSnapshot(
        get_pendientes_query_gateway(),
        SqlAlchemyPendientesSnapshotRepository(session),
        pst_lookup=SqlAlchemyPrestadorLookup(session),
        meses_corte=settings.pendientes_meses_corte,
    )


def build_get_pendientes_resumen(session: AsyncSession) -> GetPendientesResumen:
    return GetPendientesResumen(
        SqlAlchemyPendientesSnapshotRepository(session),
        build_refresh_pendientes_snapshot(session),
    )


def build_list_pendientes(session: AsyncSession) -> ListPendientes:
    return ListPendientes(
        SqlAlchemyPendientesSnapshotRepository(session),
        build_refresh_pendientes_snapshot(session),
    )
