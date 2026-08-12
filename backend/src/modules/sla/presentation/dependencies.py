"""Factory del gateway de sla. Singleton de proceso (`lru_cache`) como los
gateways de insumos (ver wiring.py de ese módulo); acá no hay token que
cachear, pero tampoco hay razón para rearmar el connection string por request.

`lru_cache` no cachea excepciones: si MERCURIO no está configurado, cada
request reintenta la factory y devuelve el 502 con mensaje claro."""

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
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string


@lru_cache
def get_sla_query_gateway() -> PyodbcSlaQueryGateway:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise ExternalServiceError(
            "La conexión a Siges (MERCURIO) no está configurada — falta SLA_MERCURIO_HOST"
        )
    return PyodbcSlaQueryGateway(
        build_mercurio_connection_string(settings), settings.sla_mercurio_timeout_seconds
    )


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
