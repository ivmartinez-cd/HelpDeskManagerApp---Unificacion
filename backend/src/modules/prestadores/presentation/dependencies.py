"""Factory del gateway de Siges para prestadores. Singleton de proceso
(`lru_cache`) — mismo criterio que `sla.presentation.dependencies`: no hay
nada que cachear salvo evitar rearmar el connection string por request."""

from functools import lru_cache

from src.modules.prestadores.infrastructure.siges.pyodbc_prestador_gateway import (
    PyodbcPrestadorGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string


@lru_cache
def get_prestador_siges_gateway() -> PyodbcPrestadorGateway:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise ExternalServiceError(
            "La conexión a Siges (MERCURIO) no está configurada — falta SLA_MERCURIO_HOST"
        )
    return PyodbcPrestadorGateway(
        build_mercurio_connection_string(settings), settings.sla_mercurio_timeout_seconds
    )
