"""Adapter zeep del puerto `IncidentesGateway` (wsAyC, solo lectura).

Cliente del provider compartido (ADR-018): WSDL parseado una vez, Session por
llamada, sin reintentos de transporte, timeout explícito. zeep es sincrónico:
cada llamada corre en `asyncio.to_thread`, acotada por un semáforo (el legacy
usaba 4 en paralelo) porque un mes de N incidentes cuesta 1 + 2×N llamadas.

Caché en memoria como el legacy: empresas 1 h, el resto `ttl_segundos`
(15 min). Reintentos: el transporte compartido no reintenta nunca (por las
escrituras de insumos); acá TODAS las operaciones son lecturas, así que se
reintentan hasta 2 veces con espera creciente ante errores de red/proxy/timeout
(el legacy lo hacía 3 veces): un reporte son ~600 llamadas y un corte momentáneo
del proxy corporativo en una sola tiraba todo (visto el 2026-09-25). Un fault
SOAP o un error de negocio no se reintenta."""

import asyncio
import logging
import random
from datetime import date
from typing import Any

import requests

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
_REINTENTOS = 2
_ESPERA_BASE_SEGUNDOS = 1.0


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
                return await self._con_reintentos(operacion, kwargs)
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

    async def _con_reintentos(self, operacion: str, kwargs: dict[str, str]) -> object:
        for intento in range(_REINTENTOS + 1):
            try:
                return await asyncio.to_thread(self._invocar, operacion, kwargs)
            except requests.exceptions.RequestException as exc:
                if intento == _REINTENTOS:
                    raise
                logger.info(
                    "wsAyC %s: error de red, reintento %d", operacion, intento + 1,
                    extra={"operacion": operacion, "error": repr(exc)},
                )
                await asyncio.sleep(_ESPERA_BASE_SEGUNDOS * 2**intento + random.random())
        raise AssertionError("inalcanzable")

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
