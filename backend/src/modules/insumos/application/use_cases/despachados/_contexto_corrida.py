"""Qué día es "hoy" y con qué feriados se clasifica una corrida de Despachados."""

import logging
from datetime import date, timedelta

from src.modules.insumos.application.use_cases.despachados.puertos_sincronizacion import (
    ConfigSincronizacion,
    SincronizarDespachosPorts,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ContextoClasificacion,
)

logger = logging.getLogger(__name__)

FERIADOS_HACIA_ATRAS = timedelta(days=400)
"""Cubre la `FechaEstado` de envíos abiertos viejos: los días sin movimiento se cuentan
desde ahí."""
FERIADOS_HACIA_ADELANTE = timedelta(days=60)
"""Cubre la fecha límite de retiro (5 días hábiles) aunque caigan varios feriados."""
AVISO_ANIO_SIGUIENTE = timedelta(days=30)
"""A menos de 30 días de fin de año también se avisa si falta cargar el año que viene."""


async def armar_contexto(
    ports: SincronizarDespachosPorts, config: ConfigSincronizacion
) -> ContextoClasificacion:
    hoy = ports.reloj().astimezone(config.zona_horaria).date()
    feriados = await ports.feriados.feriados_entre(
        hoy - FERIADOS_HACIA_ATRAS, hoy + FERIADOS_HACIA_ADELANTE
    )
    _avisar_anios_sin_feriados(hoy, feriados)
    return ContextoClasificacion(
        hoy=hoy, feriados=feriados, dias_sin_movimiento=config.dias_sin_movimiento
    )


def _avisar_anios_sin_feriados(hoy: date, feriados: frozenset[date]) -> None:
    """Sin feriados cargados las cuentas de días hábiles solo saltean fines de semana: no
    corta la corrida, pero alguien tiene que cargarlos."""
    anios_cargados = {feriado.year for feriado in feriados}
    for anio in sorted({hoy.year, (hoy + AVISO_ANIO_SIGUIENTE).year} - anios_cargados):
        logger.warning(
            "Despachados: no hay feriados cargados para %s; los días hábiles solo saltean "
            "sábados y domingos hasta que se carguen",
            anio,
        )
