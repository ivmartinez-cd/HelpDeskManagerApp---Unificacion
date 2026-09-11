"""Factory compartida del OrionQueryRunner (ADR-018).

Singleton de proceso (`lru_cache`): un solo runner → un solo semáforo de
concurrencia para todas las consultas a ORION de la app. `lru_cache` no
cachea excepciones: si ORION no está configurado, cada request reintenta la
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
from src.shared.infrastructure.orion.connection import build_orion_connection_string
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner


@lru_cache
def require_orion_runner() -> OrionQueryRunner:
    settings = get_settings()
    if not settings.orion_host:
        raise ExternalServiceError(
            "La conexión a Siges (ORION) no está configurada — falta ORION_HOST"
        )
    return OrionQueryRunner(
        build_orion_connection_string(settings),
        settings.orion_timeout_seconds,
        max_concurrent=settings.orion_max_concurrent,
    )
