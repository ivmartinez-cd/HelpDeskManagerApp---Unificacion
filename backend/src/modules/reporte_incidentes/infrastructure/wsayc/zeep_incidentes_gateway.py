"""Adapter zeep del puerto `IncidentesGateway` (wsAyC, solo lectura).

Cliente del provider compartido (ADR-018): WSDL parseado una vez, Session por
llamada, sin reintentos de transporte, timeout explícito. zeep es sincrónico:
cada llamada corre en `asyncio.to_thread`, acotada por un semáforo (el legacy
usaba 4 en paralelo) porque un mes de N incidentes cuesta 1 + 2×N llamadas.

Caché en memoria como el legacy: empresas 1 h, el resto `ttl_segundos`
(15 min). Divergencia consciente: el legacy reintentaba 3 veces ante 429/5xx;
acá un fallo se propaga como `ExternalServiceError` (el transporte compartido
no reintenta nunca) y el usuario vuelve a pedir el reporte."""

import asyncio
import logging
from datetime import date
from typing import Any

from src.modules.reporte_incidentes.domain.entities.incidente import (
    DetalleIncidente,
    Empresa,
    Incidente,
    Trabajo,
)
from src.modules.reporte_incidentes.infrastructure.wsayc import parsing, parsing_incidentes
from src.shared.domain.errors import AppError, ExternalServiceError
from src.shared.infrastructure.cache.ttl_cache import TTLCache
from src.shared.infrastructure.wsayc.client_provider import WsAycClientProvider

logger = logging.getLogger(__name__)

_TTL_EMPRESAS_SEGUNDOS = 3600


class ZeepIncidentesGateway:
    def __init__(
        self, provider: WsAycClientProvider, concurrencia: int, ttl_segundos: float
    ) -> None:
        self._provider = provider
        self._semaforo = asyncio.Semaphore(concurrencia)
        self._empresas: TTLCache[str, list[Empresa]] = TTLCache(_TTL_EMPRESAS_SEGUNDOS)
        self._respuestas: TTLCache[tuple[str, str, str], object] = TTLCache(ttl_segundos)

    async def listar_empresas(self) -> list[Empresa]:
        return await self._empresas.get_or_compute("todas", self._bajar_empresas)

    async def incidentes_recientes(self, empresa: Empresa, top: int) -> list[Incidente]:
        raw = await self._cacheada("getTopIncidents", empresa.id, str(top))
        return parsing_incidentes.incidentes(raw, empresa)

    async def trabajos(self, incidente_id: str) -> list[Trabajo]:
        return parsing.trabajos(await self._cacheada("getIncidentInstances", incidente_id, "50"))

    async def detalle(self, incidente_id: str) -> DetalleIncidente:
        return parsing.detalle(await self._cacheada("getIncidentById", incidente_id, ""))

    async def _bajar_empresas(self) -> list[Empresa]:
        # usuario_id vacío => el servicio devuelve TODOS los clientes.
        raw = await self._llamar("getEmpresas", usuario_id="")
        hoy = date.today().strftime("%Y%m%d")
        filas = parsing.filas(raw, "getEmpresas", "Empresa")
        return [e for f in filas if (e := parsing.empresa_activa(f, hoy)) is not None]

    async def _cacheada(self, operacion: str, clave: str, extra: str) -> object:
        async def pedir() -> object:
            return await self._llamar(operacion, **_argumentos(operacion, clave, extra))

        return await self._respuestas.get_or_compute((operacion, clave, extra), pedir)

    async def _llamar(self, operacion: str, **kwargs: str) -> object:
        async with self._semaforo:
            try:
                return await asyncio.to_thread(self._invocar, operacion, kwargs)
            except AppError:
                raise
            except Exception as exc:
                logger.warning(
                    "wsAyC %s falló", operacion,
                    extra={"operacion": operacion, "argumentos": kwargs}, exc_info=exc,
                )
                raise ExternalServiceError(
                    "No se pudo consultar wsAyC de Canal Directo. Probá de nuevo en unos minutos."
                ) from exc

    def _invocar(self, operacion: str, kwargs: dict[str, str]) -> Any:
        return getattr(self._provider.service(), operacion)(**kwargs)


def _argumentos(operacion: str, clave: str, extra: str) -> dict[str, str]:
    if operacion == "getTopIncidents":
        # OrderBy vacío => el servicio ordena del más reciente al más viejo.
        return {
            "IdEmpresa": clave, "IdSucursal": "", "IdSector": "",
            "OrderBy": "", "Top": extra, "IdEstado": "",
        }
    if operacion == "getIncidentInstances":
        # Sin `top` el servicio no devuelve filas.
        return {"id": clave, "top": extra}
    return {"id": clave}
