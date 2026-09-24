"""Caso de uso SincronizarDespachos — una corrida del job de Despachados, programada o
disparada con "Actualizar ahora": da de alta en HDM las guías OCA que despachó Siges y
consulta en OCA el estado actual de los envíos abiertos.

Secuencial y pausado a propósito (como `verify_offline_devices`): OCA es un webservice
público y no hay que martillarlo. Confirma después de cada guía, así lo consultado queda
guardado aunque la corrida se corte, y corre con un candado: el job programado y el botón
nunca se pisan. La pantalla lee siempre de la base de HDM, nunca espera a esta corrida.
"""

import logging

from src.modules.insumos.application.use_cases.despachados._lote_despachos import (
    AvanceCorrida,
    LoteDespachos,
)
from src.modules.insumos.application.use_cases.despachados.puertos_sincronizacion import (
    ConfigSincronizacion,
    SincronizarDespachosPorts,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.domain.errores_despachados import SincronizacionDespachosEnCursoError

__all__ = [
    "MOTIVO_INTERRUMPIDA",
    "ConfigSincronizacion",
    "SincronizarDespachos",
    "SincronizarDespachosPorts",
]

logger = logging.getLogger(__name__)

MOTIVO_INTERRUMPIDA = "Interrumpida: el proceso se reinició durante la corrida"
"""Error con el que se cierran las corridas que quedaron sin terminar: si el candado está
libre, ninguna otra corrida está en curso."""


class SincronizarDespachos:
    def __init__(self, ports: SincronizarDespachosPorts, config: ConfigSincronizacion) -> None:
        self._ports = ports
        self._config = config

    async def execute(
        self, origen: OrigenCorrida, usuario_nombre: str | None = None
    ) -> ResumenCorrida:
        """Corre la sincronización y devuelve su resumen. `usuario_nombre` es quien apretó
        "Actualizar ahora" (None en las programadas). Si ya hay una corrida en curso lanza
        `SincronizacionDespachosEnCursoError` sin tocar nada: la que corre termina sola."""
        async with self._ports.candado.hold() as obtenido:
            if not obtenido:
                raise SincronizacionDespachosEnCursoError()
            corrida = await self._iniciar(origen, usuario_nombre)
            return await self._correr(corrida)

    async def _iniciar(self, origen: OrigenCorrida, usuario_nombre: str | None) -> Corrida:
        await self._ports.corridas.cerrar_interrumpidas(MOTIVO_INTERRUMPIDA)
        corrida = await self._ports.corridas.iniciar(origen, usuario_nombre)
        await self._ports.confirmar()
        return corrida

    async def _correr(self, corrida: Corrida) -> ResumenCorrida:
        """Un error inesperado (no de Siges ni de OCA) corta la corrida: se descarta lo no
        confirmado, queda registrado en ella con lo que llegó a hacer y se relanza."""
        lote = LoteDespachos(self._ports, self._config)
        try:
            await lote.ejecutar()
        except Exception as exc:
            logger.error(
                "Despachados: la corrida %s se cortó por un error inesperado",
                corrida.id,
                exc_info=exc,
            )
            lote.avance.agregar_error(f"{type(exc).__name__}: {exc}")
            await self._terminar_tras_fallo(corrida, lote.avance)
            raise
        resumen = lote.avance.a_resumen()
        await self._terminar(corrida, resumen)
        return resumen

    async def _terminar(self, corrida: Corrida, resumen: ResumenCorrida) -> None:
        await self._ports.corridas.terminar(corrida.id, resumen)
        await self._ports.confirmar()

    async def _terminar_tras_fallo(self, corrida: Corrida, avance: AvanceCorrida) -> None:
        """Descarta lo que quedó a medio escribir y registra el final con el error. Si ni
        siquiera eso se puede (p. ej. la base se cayó), la corrida queda abierta y la próxima
        la cierra como interrumpida; el error original sigue."""
        try:
            await self._ports.revertir()
            await self._terminar(corrida, avance.a_resumen())
        except Exception as exc:
            logger.error(
                "Despachados: no se pudo registrar el final de la corrida %s; la próxima la "
                "cierra como interrumpida",
                corrida.id,
                exc_info=exc,
            )
