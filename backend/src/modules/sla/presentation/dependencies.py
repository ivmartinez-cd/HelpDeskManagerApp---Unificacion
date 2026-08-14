"""Factory del gateway de sla. Singleton de proceso (`lru_cache`) como los
gateways de insumos (ver wiring.py de ese módulo). El chequeo de host y el
runner con su semáforo viven en `require_mercurio_runner` (ADR-018), que
tampoco cachea excepciones: sin MERCURIO configurado cada request reintenta y
devuelve el 502 con mensaje claro."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sla.application.use_cases.get_sla_compliance import GetSlaCompliance
from src.modules.sla.application.use_cases.list_incidentes_vencidos import (
    ListIncidentesVencidos,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.infrastructure.mercurio.pyodbc_sla_query_gateway import (
    PyodbcSlaQueryGateway,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_sla_snapshot_repository import (
    SqlAlchemySlaSnapshotRepository,
)
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner


@lru_cache
def get_sla_query_gateway() -> PyodbcSlaQueryGateway:
    return PyodbcSlaQueryGateway(require_mercurio_runner())


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
