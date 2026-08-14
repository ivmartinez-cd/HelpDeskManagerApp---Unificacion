"""Factories de gateways del módulo contra Siges (ver ADR-012). Mismo patrón
que sla/presentation/dependencies.py: singleton de proceso (`lru_cache`); el
chequeo de host y el runner compartido vienen de `require_mercurio_runner`
(ADR-018)."""

import logging
from functools import lru_cache

from src.modules.contadores.infrastructure.siges.pyodbc_anexos_pendientes_gateway import (
    PyodbcAnexosPendientesGateway,
)
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
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner

logger = logging.getLogger(__name__)

# La consulta de equipos sin real recorre Contadores completo (medido: ~10s);
# el timeout general de 30s queda justo si MERCURIO está cargado, y por eso
# tiene el suyo propio. El TTL de la caché hace que el costo se pague una vez
# por ventana de trabajo, no por interacción (refresh manual aparte).
_EQUIPOS_SIN_REAL_TIMEOUT_SECONDS = 120.0
_EQUIPOS_SIN_REAL_CACHE_TTL_SECONDS = 600.0

# La consulta de anexos pendientes es liviana (~50 filas sobre Factura_Anexo
# indexada) — alcanza el timeout general del runner; el TTL corto mantiene el
# reporte fresco durante la ventana de cierre sin repetir consultas por cada
# interacción de la UI.
_ANEXOS_PENDIENTES_CACHE_TTL_SECONDS = 300.0


@lru_cache
def get_operador_catalog_gateway() -> PyodbcOperadorGateway:
    return PyodbcOperadorGateway(require_mercurio_runner())


@lru_cache
def get_equipos_sin_real_gateway() -> PyodbcEquiposSinRealGateway:
    return PyodbcEquiposSinRealGateway(
        require_mercurio_runner(),
        _EQUIPOS_SIN_REAL_TIMEOUT_SECONDS,
        _EQUIPOS_SIN_REAL_CACHE_TTL_SECONDS,
    )


@lru_cache
def get_anexos_pendientes_gateway() -> PyodbcAnexosPendientesGateway:
    return PyodbcAnexosPendientesGateway(
        require_mercurio_runner(), _ANEXOS_PENDIENTES_CACHE_TTL_SECONDS
    )


@lru_cache
def get_parque_cliente_gateway() -> PyodbcParqueClienteGateway:
    return PyodbcParqueClienteGateway(require_mercurio_runner())


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
