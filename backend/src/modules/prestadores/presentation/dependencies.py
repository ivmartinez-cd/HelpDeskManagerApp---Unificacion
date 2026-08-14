"""Factory del gateway de Siges para prestadores. Singleton de proceso
(`lru_cache`) — mismo criterio que `sla.presentation.dependencies`; el chequeo
de host y el runner compartido vienen de `require_mercurio_runner` (ADR-018)."""

import logging
from functools import lru_cache

from src.modules.prestadores.infrastructure.siges.pyodbc_prestador_gateway import (
    PyodbcPrestadorGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner

logger = logging.getLogger(__name__)


@lru_cache
def get_prestador_siges_gateway() -> PyodbcPrestadorGateway:
    return PyodbcPrestadorGateway(require_mercurio_runner())


def get_prestador_siges_gateway_or_none() -> PyodbcPrestadorGateway | None:
    """Variante para consumidores que degradan sin Siges (el listado, que
    muestra el último parque persistido) en lugar de fallar — el sync sigue
    usando la variante estricta porque sin MERCURIO no tiene nada que hacer."""
    try:
        return get_prestador_siges_gateway()
    except ExternalServiceError as exc:
        logger.warning("Siges (MERCURIO) no configurado; se sigue sin conteo en vivo", exc_info=exc)
        return None
