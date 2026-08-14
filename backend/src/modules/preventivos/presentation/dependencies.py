"""Factory del gateway del módulo contra Siges — mismo patrón que
contadores/presentation/dependencies.py: singleton de proceso (`lru_cache`),
runner compartido vía `require_mercurio_runner` (ADR-018)."""

from functools import lru_cache

from src.modules.preventivos.infrastructure.siges.pyodbc_preventivos_gateway import (
    PyodbcPreventivosGateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner

# La consulta por zona es liviana (0.2-0.4 s medidos) — alcanza el timeout
# general del runner. El TTL corto solo evita repetir la consulta en cada
# paginación/filtro de la misma pantalla; el botón "Actualizar" fuerza refresh.
_CACHE_TTL_SECONDS = 300.0


@lru_cache
def get_preventivos_gateway() -> PyodbcPreventivosGateway:
    return PyodbcPreventivosGateway(require_mercurio_runner(), _CACHE_TTL_SECONDS)


@lru_cache
def get_zonas_excluidas() -> tuple[str, ...]:
    raw = get_settings().preventivos_zonas_excluidas
    return tuple(p.strip() for p in raw.split(",") if p.strip())
