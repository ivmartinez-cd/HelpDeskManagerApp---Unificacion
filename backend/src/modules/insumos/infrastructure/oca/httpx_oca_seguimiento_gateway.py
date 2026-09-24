"""Adapter httpx del puerto OcaSeguimientoGateway (webservice e-Pak de OCA).

`GetEnvioEstadoActual` es un GET público, sin credenciales y de solo lectura, así que
reintentarlo no tiene efectos dobles: reintentos cortos (0,5 s y 1 s, como Insight) solo
ante 429/5xx o fallas de transporte, para que un tropiezo puntual de OCA no deje una guía
sin actualizar. Cualquier otra respuesta de error se reporta sin reintentar. La pausa
entre guías (0,3 s) no vive acá: la maneja el job que recorre el lote.

- User-Agent propio: el proxy corporativo rechazó el UA por defecto de httpx en WATI.
- `trust_env=True` (default de httpx): sale a Internet por HTTPS_PROXY, como WATI.
- httpx no sigue redirecciones por defecto: una 3xx también se trata como falla.
"""

import asyncio
import logging

import httpx

from src.modules.insumos.domain.errores_despachados import RespuestaOcaInvalidaError
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from src.modules.insumos.infrastructure.oca.parseo_estado_oca import parsear_estado_actual
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_USER_AGENT = "helpdesk-manager/1.0 (+insumos-despachados)"
_ESTADOS_REINTENTABLES = frozenset({429, 500, 502, 503, 504})
_ESPERAS_REINTENTO_SEGUNDOS = (0.5, 1.0)


class HttpxOcaSeguimientoGateway:
    def __init__(
        self,
        url: str,
        timeout_segundos: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._url = url
        self._client = httpx.AsyncClient(
            headers={"User-Agent": _USER_AGENT},
            timeout=httpx.Timeout(timeout_segundos, connect=5.0),
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def consultar_estado_actual(self, guia: str) -> EstadoOca | None:
        try:
            respuesta = await self._get_con_reintentos(guia)
        except httpx.HTTPError as exc:
            detalle = _describir(exc)
            logger.error(
                "No se pudo consultar OCA para la guía %s (%s)", guia, detalle, exc_info=exc
            )
            raise ExternalServiceError(
                f"No se pudo consultar OCA para la guía {guia}: {detalle}"
            ) from exc
        return _parsear(respuesta, guia)

    async def _get_con_reintentos(self, guia: str) -> httpx.Response:
        for espera in _ESPERAS_REINTENTO_SEGUNDOS:
            respuesta = await self._intentar(guia)
            if respuesta is not None:
                return respuesta
            await asyncio.sleep(espera)
        return await self._get(guia)

    async def _intentar(self, guia: str) -> httpx.Response | None:
        """La respuesta, o None ante una falla transitoria (el caller reintenta).
        Las fallas no reintentables se relanzan."""
        try:
            return await self._get(guia)
        except httpx.HTTPError as exc:
            if not _es_reintentable(exc):
                raise
            logger.warning("OCA falló para la guía %s (%s); se reintenta", guia, _describir(exc))
            return None

    async def _get(self, guia: str) -> httpx.Response:
        respuesta = await self._client.get(
            self._url, params={"numeroEnvio": guia, "ordenRetiro": ""}
        )
        respuesta.raise_for_status()
        return respuesta


def _es_reintentable(exc: httpx.HTTPError) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _ESTADOS_REINTENTABLES
    return isinstance(exc, httpx.TransportError)


def _describir(exc: httpx.HTTPError) -> str:
    """Con el comienzo del cuerpo en los errores HTTP: en un servicio ASMX es lo único que
    dice la causa (p. ej. "System.InvalidOperationException: Request format is invalid")."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}: {exc.response.text[:200]!r}"
    return f"{type(exc).__name__}: {exc}"


def _parsear(respuesta: httpx.Response, guia: str) -> EstadoOca | None:
    """El error ya trae el valor ilegible (o el comienzo del cuerpo si no era un DataSet):
    no se loguea el cuerpo entero, que en una respuesta válida lleva datos del destinatario."""
    try:
        return parsear_estado_actual(respuesta.content, guia)
    except RespuestaOcaInvalidaError as exc:
        logger.error("OCA devolvió una respuesta ilegible para la guía %s: %s", guia, exc.message)
        raise
