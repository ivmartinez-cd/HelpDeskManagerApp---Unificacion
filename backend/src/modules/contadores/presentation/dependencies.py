"""Factories de gateways del módulo contra Siges (ver ADR-012). Mismo patrón
que sla/presentation/dependencies.py: singleton de proceso (`lru_cache`),
fail-fast si MERCURIO no está configurado."""

import logging
from functools import lru_cache

from src.modules.contadores.infrastructure.siges.pyodbc_equipos_sin_real_gateway import (
    PyodbcEquiposSinRealGateway,
)
from src.modules.contadores.infrastructure.siges.pyodbc_operador_gateway import (
    PyodbcOperadorGateway,
)
from src.modules.contadores.infrastructure.siges.pyodbc_parque_cliente_gateway import (
    PyodbcParqueClienteGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

logger = logging.getLogger(__name__)

# La consulta de equipos sin real recorre Contadores completo (medido: ~10s);
# el timeout general de 30s queda justo si MERCURIO está cargado, y por eso
# tiene el suyo propio. El TTL de la caché hace que el costo se pague una vez
# por ventana de trabajo, no por interacción (refresh manual aparte).
_EQUIPOS_SIN_REAL_TIMEOUT_SECONDS = 120.0
_EQUIPOS_SIN_REAL_CACHE_TTL_SECONDS = 600.0


def _require_mercurio_connection_string() -> str:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise ExternalServiceError(
            "La conexión a Siges (MERCURIO) no está configurada — falta SLA_MERCURIO_HOST"
        )
    return build_mercurio_connection_string(settings)


@lru_cache
def get_operador_catalog_gateway() -> PyodbcOperadorGateway:
    return PyodbcOperadorGateway(
        _require_mercurio_connection_string(), get_settings().sla_mercurio_timeout_seconds
    )


@lru_cache
def get_equipos_sin_real_gateway() -> PyodbcEquiposSinRealGateway:
    return PyodbcEquiposSinRealGateway(
        _require_mercurio_connection_string(),
        _EQUIPOS_SIN_REAL_TIMEOUT_SECONDS,
        _EQUIPOS_SIN_REAL_CACHE_TTL_SECONDS,
    )


@lru_cache
def get_parque_cliente_gateway() -> PyodbcParqueClienteGateway:
    return PyodbcParqueClienteGateway(
        _require_mercurio_connection_string(), get_settings().sla_mercurio_timeout_seconds
    )


def get_parque_cliente_gateway_or_none() -> PyodbcParqueClienteGateway | None:
    """Variante para la card de Inicio, que degrada a solo clientes sin Siges
    en lugar de fallar (mismo criterio que el listado de prestadores). La
    búsqueda del modal de resolución usa la variante estricta: sin MERCURIO
    no tiene nada que buscar."""
    try:
        return get_parque_cliente_gateway()
    except ExternalServiceError as exc:
        logger.warning(
            "Siges (MERCURIO) no configurado; la card de clientes va sin impresoras",
            exc_info=exc,
        )
        return None
