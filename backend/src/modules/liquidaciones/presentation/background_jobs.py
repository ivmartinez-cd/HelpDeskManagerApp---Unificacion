"""Job de fondo del módulo liquidaciones:

- liquidaciones_reconciliar: cada 120 min (2 h, configurable) — mismo caso de
  uso que el botón "Sincronizar CD" (`SincronizarLiquidaciones`), pero con
  `permitir_eliminar_anuladas=False`: nunca borra liquidaciones. La detección
  de anuladas queda exclusiva del botón/endpoint manual, donde hay un usuario
  mirando — un ciclo automático de madrugada no es el lugar para una operación
  irreversible que se lleva incidentes/alertas por CASCADE.

Corre bajo DISABLE_BACKGROUND_JOBS igual que los demás módulos (CLAUDE.md).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from src.modules.liquidaciones.presentation.dependencies import (
    build_sincronizar_liquidaciones,
)
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


async def _loop(
    nombre: str, ciclo: Callable[[], Awaitable[None]], interval_minutes: int
) -> None:
    """Corre `ciclo` cada `interval_minutes`; un ciclo fallido se loguea y se
    reintenta en el próximo intervalo, nunca corta el loop."""
    logger.info("%s: iniciando (intervalo %d min)", nombre, interval_minutes)
    while True:
        try:
            await ciclo()
        except Exception as exc:
            logger.error("%s: ciclo fallido", nombre, exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


async def _ciclo_reconciliar() -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        use_case = build_sincronizar_liquidaciones(session)
        resultado = await use_case.execute(permitir_eliminar_anuladas=False)
        await session.commit()
    logger.info(
        "liquidaciones_reconciliar: OK — creadas=%d reconciliadas=%d "
        "estados_actualizados=%d extras_actualizados=%d facturas_actualizadas=%d fallidas=%d",
        resultado.creadas,
        resultado.reconciliadas,
        resultado.estados_actualizados,
        resultado.extras_actualizados,
        resultado.facturas_actualizadas,
        resultado.fallidas,
    )


async def background_liquidaciones_reconciliar_task(interval_minutes: int) -> None:
    await _loop("liquidaciones_reconciliar", _ciclo_reconciliar, interval_minutes)


def start_liquidaciones_background_jobs(interval_minutes: int) -> list[asyncio.Task[None]]:
    return [asyncio.create_task(background_liquidaciones_reconciliar_task(interval_minutes))]
