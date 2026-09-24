"""Job de fondo de Insumos > Despachados y el disparo de "Actualizar ahora".

El job corre `SincronizarDespachos` cada `DESPACHADOS_INTERVALO_MINUTOS`, pero solo dentro
de la ventana configurada (días y horas en hora Argentina): fuera de ella deja una línea de
log y espera al próximo ciclo. El primer ciclo, inmediato al arrancar, también respeta la
ventana. Cada corrida usa su propia sesión (confirma después de cada guía).

"Actualizar ahora" corre el mismo caso de uso en una tarea aparte, sin esperar la ventana:
el candado del caso de uso garantiza que nunca se pise con el job.

Ninguna corrida fallida corta el loop: se loguea y se reintenta en el próximo intervalo.
"""

import asyncio
import logging
from datetime import datetime

from src.modules.insumos.domain.entities.despachados.corrida import OrigenCorrida, ResumenCorrida
from src.modules.insumos.domain.errores_despachados import SincronizacionDespachosEnCursoError
from src.modules.insumos.domain.services.despachados.ventana_job import (
    VentanaJob,
    dentro_de_ventana,
)
from src.modules.insumos.presentation.dependencies.despachados import (
    build_sincronizar_despachos,
)
from src.modules.insumos.presentation.wiring import app_timezone
from src.shared.infrastructure.config.settings import Settings
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)

_tareas_manuales: set[asyncio.Task[None]] = set()
"""Referencias fuertes a las corridas manuales en curso: sin ellas el event loop solo
guarda una referencia débil y la tarea podría recolectarse a mitad de camino."""


def _ahora() -> datetime:
    """Hora actual en la zona de negocio (la ventana se mide en hora Argentina)."""
    return datetime.now(app_timezone())


def ventana_desde(settings: Settings) -> VentanaJob:
    """Ventana del job según settings (valida días y horas al arrancar)."""
    return VentanaJob(
        dias_semana=frozenset(settings.despachados_dias_semana),
        hora_inicio=settings.despachados_hora_inicio,
        hora_fin=settings.despachados_hora_fin,
    )


def start_despachados_background_jobs(settings: Settings) -> list[asyncio.Task[None]]:
    """Arranca el loop del job programado de Despachados."""
    ventana = ventana_desde(settings)
    intervalo = settings.despachados_intervalo_minutos
    return [asyncio.create_task(_loop(ventana, intervalo))]


def lanzar_actualizacion_manual(usuario_nombre: str) -> None:
    """Dispara "Actualizar ahora" en segundo plano y vuelve enseguida; la tarea queda
    referenciada en `_tareas_manuales` hasta que termina."""
    tarea = asyncio.create_task(_correr(OrigenCorrida.MANUAL, usuario_nombre))
    _tareas_manuales.add(tarea)
    tarea.add_done_callback(_tareas_manuales.discard)


async def _loop(ventana: VentanaJob, intervalo_minutos: int) -> None:
    """Un ciclo (si cae en la ventana) y la espera del intervalo, para siempre."""
    logger.info("despachados: iniciando (intervalo %d min)", intervalo_minutos)
    while True:
        await _ciclo_programado(ventana)
        await asyncio.sleep(intervalo_minutos * 60)


async def _ciclo_programado(ventana: VentanaJob) -> None:
    """Corre la sincronización programada solo si ahora cae dentro de la ventana."""
    ahora = _ahora()
    if not dentro_de_ventana(ahora, ventana):
        logger.info(
            "despachados: fuera de ventana (%s), no se consulta",
            ahora.isoformat(timespec="minutes"),
        )
        return
    await _correr(OrigenCorrida.PROGRAMADA, None)


async def _correr(origen: OrigenCorrida, usuario_nombre: str | None) -> None:
    """Una corrida; nunca propaga: "en curso" es esperable, lo demás se loguea con traza."""
    try:
        resumen = await _sincronizar(origen, usuario_nombre)
    except SincronizacionDespachosEnCursoError:
        logger.info("despachados: ya hay una corrida en curso; se omite la %s", origen.value)
        return
    except Exception as exc:
        logger.error("despachados: la corrida %s falló", origen.value, exc_info=exc)
        return
    _loguear_resumen(origen, resumen)


async def _sincronizar(origen: OrigenCorrida, usuario_nombre: str | None) -> ResumenCorrida:
    """Arma el caso de uso sobre una sesión propia de la corrida y lo ejecuta."""
    async with get_sessionmaker()() as session:
        return await build_sincronizar_despachos(session).execute(origen, usuario_nombre)


def _loguear_resumen(origen: OrigenCorrida, resumen: ResumenCorrida) -> None:
    """Una línea con lo que hizo la corrida (y el error parcial, si lo hubo)."""
    logger.info(
        "despachados: corrida %s OK — nuevos=%d consultas_ok=%d consultas_error=%d error=%s",
        origen.value,
        resumen.envios_nuevos,
        resumen.consultas_ok,
        resumen.consultas_error,
        resumen.error,
    )
