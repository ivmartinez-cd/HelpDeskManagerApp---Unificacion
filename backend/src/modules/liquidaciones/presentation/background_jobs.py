"""Jobs de fondo del módulo liquidaciones:

- liquidaciones_reconciliar: cada 120 min (2 h, configurable) — mismo caso de
  uso que el botón "Sincronizar CD" (`SincronizarLiquidaciones`), pero con
  `permitir_eliminar_anuladas=False`: nunca borra liquidaciones. La detección
  de anuladas queda exclusiva del botón/endpoint manual, donde hay un usuario
  mirando — un ciclo automático de madrugada no es el lugar para una operación
  irreversible que se lleva incidentes/alertas por CASCADE.
- liquidaciones_sync_tarifarios: cada 1440 min (1 día, configurable) — mismo
  caso de uso que el botón "Sincronizar desde Siges" de Tarifarios en modo
  aplicar (`SyncTarifariosDesdeSiges`): crea solo las vigencias que faltan,
  nunca pisa un conflicto local≠Siges (queda logueado y visible en el modal).
  Si creó algo, reanaliza las liquidaciones abiertas para que las alertas de
  precio/tarifario se actualicen solas. Solo lectura contra Siges.

Corren bajo DISABLE_BACKGROUND_JOBS igual que los demás módulos (CLAUDE.md).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from src.modules.liquidaciones.application.dtos.siges_tarifarios import (
    SyncTarifariosResultado,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_reanalizar_liquidaciones_abiertas,
    build_sincronizar_liquidaciones,
    build_sync_tarifarios_desde_siges,
)
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


async def _loop(nombre: str, ciclo: Callable[[], Awaitable[None]], interval_minutes: int) -> None:
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


async def _ciclo_sync_tarifarios() -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        resultado = await build_sync_tarifarios_desde_siges(session).execute(dry_run=False)
        if resultado.creados:
            await build_reanalizar_liquidaciones_abiertas(session).execute(None)
        await session.commit()
    _log_sync_tarifarios(resultado)


def _log_sync_tarifarios(resultado: SyncTarifariosResultado) -> None:
    logger.info(
        "liquidaciones_sync_tarifarios: OK — creadas=%d sin_cambios=%d conflictos=%d "
        "zonas_sin_mapear=%d sin_vinculo=%d sin_generica=%d",
        resultado.creados,
        resultado.sin_cambios,
        len(resultado.conflictos),
        len(resultado.zonas_sin_mapear),
        len(resultado.prestadores_sin_vinculo),
        len(resultado.prestadores_sin_generica),
    )
    _warn_pendientes_de_la_ui(resultado)


def _warn_pendientes_de_la_ui(resultado: SyncTarifariosResultado) -> None:
    """Lo que el job no puede resolver solo y alguien tiene que mirar en la UI."""
    if resultado.conflictos:
        logger.warning(
            "liquidaciones_sync_tarifarios: %d conflicto(s) local≠Siges sin pisar",
            len(resultado.conflictos),
            extra={"prestadores": sorted({c.prestador for c in resultado.conflictos})},
        )
    if resultado.zonas_sin_mapear or resultado.prestadores_sin_generica:
        logger.warning(
            "liquidaciones_sync_tarifarios: config incompleta",
            extra={
                "zonas_sin_mapear": [
                    (z.prestador, z.descripcion_siges) for z in resultado.zonas_sin_mapear
                ],
                "prestadores_sin_generica": resultado.prestadores_sin_generica,
            },
        )


async def background_liquidaciones_reconciliar_task(interval_minutes: int) -> None:
    await _loop("liquidaciones_reconciliar", _ciclo_reconciliar, interval_minutes)


async def background_liquidaciones_sync_tarifarios_task(interval_minutes: int) -> None:
    await _loop("liquidaciones_sync_tarifarios", _ciclo_sync_tarifarios, interval_minutes)


def start_liquidaciones_background_jobs(
    interval_minutes: int, sync_tarifarios_interval_minutes: int
) -> list[asyncio.Task[None]]:
    return [
        asyncio.create_task(background_liquidaciones_reconciliar_task(interval_minutes)),
        asyncio.create_task(
            background_liquidaciones_sync_tarifarios_task(sync_tarifarios_interval_minutes)
        ),
    ]
