"""Factory del gateway de Siges para prestadores. Singleton de proceso
(`lru_cache`) — mismo criterio que `sla.presentation.dependencies`: no hay
nada que cachear salvo evitar rearmar el connection string por request."""

import logging
from functools import lru_cache

from src.modules.prestadores.infrastructure.siges.pyodbc_prestador_gateway import (
    PyodbcPrestadorGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

logger = logging.getLogger(__name__)


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


def get_prestador_siges_gateway_or_none() -> PyodbcPrestadorGateway | None:
    """Variante para consumidores que degradan sin Siges (el listado, que
    muestra el último parque persistido) en lugar de fallar — el sync sigue
    usando la variante estricta porque sin MERCURIO no tiene nada que hacer."""
    try:
        return get_prestador_siges_gateway()
    except ExternalServiceError as exc:
        logger.warning("Siges (MERCURIO) no configurado; se sigue sin conteo en vivo", exc_info=exc)
        return None
