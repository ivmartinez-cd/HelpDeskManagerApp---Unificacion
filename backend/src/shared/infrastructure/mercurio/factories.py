"""Factory compartida del MercurioQueryRunner (ADR-018).

Singleton de proceso (`lru_cache`): un solo runner → un solo semáforo de
concurrencia para todas las consultas a MERCURIO de la app. `lru_cache` no
cachea excepciones: si MERCURIO no está configurado, cada request reintenta la
factory y devuelve el 502 con mensaje claro (mismo criterio que las factories
de módulo a las que esto reemplaza).

La semántica `_or_none` (degradar con warning en vez de fallar) se queda en
las factories de gateway de cada módulo: el mensaje del warning describe qué
funcionalidad concreta degrada ("la card de clientes va sin impresoras"), y
eso no es genérico del runner.
"""

from functools import lru_cache

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


@lru_cache
def require_mercurio_runner() -> MercurioQueryRunner:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise ExternalServiceError(
            "La conexión a Siges (MERCURIO) no está configurada — falta SLA_MERCURIO_HOST"
        )
    return MercurioQueryRunner(
        build_mercurio_connection_string(settings),
        settings.sla_mercurio_timeout_seconds,
        max_concurrent=settings.mercurio_max_concurrent,
    )
