"""Plomería compartida de las consultas pyodbc a Siges/MERCURIO (ADR-018).

Todo gateway de módulo contra MERCURIO delega acá el esqueleto que antes
duplicaba: pyodbc es síncrono, así que la consulta corre en un thread
(`asyncio.to_thread`); conexión nueva por consulta a propósito (fetch
esporádico, resiliente a cortes de red/reinicios de MERCURIO sin pooling
propio — las conexiones pyodbc no son thread-safe para compartir); timeout de
login y de consulta; `pyodbc.Error` → `ExternalServiceError` con log
contextualizado (§6). El semáforo acota las consultas simultáneas de todo el
proceso (la de sla puede tardar ~40 s, la de equipos-sin-real ~10 s; sin tope,
requests de usuarios + jobs se apilaban sin cota).

Lo que NO vive acá: el SQL, el mapeo de filas y los puertos de domain — eso es
negocio de cada módulo y se queda en su infrastructure.
"""

import asyncio
import logging
import time
from collections.abc import Sequence
from typing import Any

import pyodbc

from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

DEFAULT_ERROR_MESSAGE = "No se pudo consultar la base Siges (MERCURIO)"

# Encolar detrás del semáforo no consume el timeout de login/consulta (la
# espera es previa al connect), así que un apilamiento no genera timeouts
# nuevos — pero sería invisible sin este warning.
_SEMAPHORE_WAIT_WARNING_SECONDS = 10.0


class MercurioQueryRunner:
    def __init__(
        self, connection_string: str, timeout_seconds: float, max_concurrent: int = 3
    ) -> None:
        self._connection_string = connection_string
        self._timeout_seconds = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_all(
        self,
        sql: str,
        params: Sequence[object] = (),
        *,
        gateway: str,
        log_message: str,
        log_extra: dict[str, object] | None = None,
        error_message: str = DEFAULT_ERROR_MESSAGE,
        timeout_override: float | None = None,
    ) -> list[Any]:
        """Corre un SELECT y devuelve todas las filas.

        `gateway`/`log_message`/`log_extra` contextualizan el log de error (y
        el warning de espera) sin que el gateway tenga que atrapar nada.
        `error_message` admite el placeholder `{exc}` para incluir el error de
        pyodbc en el mensaje visible (lo usa sla). `timeout_override` es para
        consultas con presupuesto propio (equipos-sin-real: 120 s).
        """
        timeout = self._timeout_seconds if timeout_override is None else timeout_override
        await self._acquire(gateway)
        try:
            return await asyncio.to_thread(self._query, sql, params, timeout)
        except pyodbc.Error as exc:
            logger.error(
                log_message, extra={**(log_extra or {}), "gateway": gateway}, exc_info=exc
            )
            raise ExternalServiceError(error_message.format(exc=exc)) from exc
        finally:
            self._semaphore.release()

    async def _acquire(self, gateway: str) -> None:
        inicio = time.monotonic()
        await self._semaphore.acquire()
        espera = time.monotonic() - inicio
        if espera >= _SEMAPHORE_WAIT_WARNING_SECONDS:
            logger.warning(
                "La consulta a Siges/MERCURIO esperó %.1f s el semáforo de concurrencia",
                espera,
                extra={"gateway": gateway},
            )

    def _query(self, sql: str, params: Sequence[object], timeout: float) -> list[Any]:
        with pyodbc.connect(
            self._connection_string, timeout=int(timeout)
        ) as connection:
            # `timeout` del connect es solo de login; este es el de la consulta.
            connection.timeout = int(timeout)
            cursor = connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return list(cursor.fetchall())
