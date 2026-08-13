"""Factory del gateway de resolución de identidad de operadores contra Siges
(ver ADR-012). Mismo patrón que sla/presentation/dependencies.py: singleton
de proceso (`lru_cache`), fail-fast si MERCURIO no está configurado."""

from functools import lru_cache

from src.modules.contadores.infrastructure.siges.pyodbc_operador_gateway import (
    PyodbcOperadorGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string


@lru_cache
def get_operador_catalog_gateway() -> PyodbcOperadorGateway:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise ExternalServiceError(
            "La conexión a Siges (MERCURIO) no está configurada — falta SLA_MERCURIO_HOST"
        )
    return PyodbcOperadorGateway(
        build_mercurio_connection_string(settings), settings.sla_mercurio_timeout_seconds
    )
