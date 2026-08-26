"""Factory del gateway del módulo contra Siges — mismo patrón que
contadores/presentation/dependencies.py: singleton de proceso (`lru_cache`),
runner compartido vía `require_mercurio_runner` (ADR-018)."""

from functools import lru_cache

from src.modules.preventivos.infrastructure.siges.pyodbc_preventivos_gateway import (
    PyodbcPreventivosGateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner

# El TTL evita repetir la consulta cara contra Siges en cada paginación/filtro
# de la misma pantalla; el botón "Actualizar" fuerza refresh. Medido en frío
# 2026-08-26 (ver docstring del gateway): 4.5 s por zona — el parque de una
# zona es el estado operativo que un usuario habilita/deshabilita, así que se
# mantiene relativamente fresco.
_CACHE_TTL_SECONDS = 300.0

# El catálogo de zonas (ZONAS_SQL, 5.2 s en frío) es un conteo agregado que
# cambia mucho menos que el parque de una zona puntual — un TTL 6x más largo
# evita pagar esa consulta cada vez que un usuario vuelve a la pantalla
# después de 5 minutos, sin perder frescura real (la lista de zonas casi
# nunca cambia y el conteo de "máquinas activas" es informativo, no operativo).
_ZONAS_CACHE_TTL_SECONDS = 1800.0


@lru_cache
def get_preventivos_gateway() -> PyodbcPreventivosGateway:
    return PyodbcPreventivosGateway(
        require_mercurio_runner(),
        _CACHE_TTL_SECONDS,
        get_settings().preventivos_meses_actividad,
        zonas_cache_ttl_seconds=_ZONAS_CACHE_TTL_SECONDS,
    )


@lru_cache
def get_zonas_excluidas() -> tuple[str, ...]:
    raw = get_settings().preventivos_zonas_excluidas
    return tuple(p.strip() for p in raw.split(",") if p.strip())
