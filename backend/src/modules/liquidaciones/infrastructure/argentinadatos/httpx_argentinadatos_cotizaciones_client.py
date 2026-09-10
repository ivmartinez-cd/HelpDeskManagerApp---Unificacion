"""Adapter de CotizacionesHistoricasProvider — api.argentinadatos.com, misma
fuente que ya usa el módulo `vacaciones` para feriados
(`ArgentinaDatosFeriadosClient`). Serie completa del oficial desde 2011 en una
sola llamada: más barato que pedir día por día para reconstruir los cierres de
mes de 2026 en adelante."""

import logging
from datetime import date

import httpx

from src.modules.liquidaciones.domain.repositories.cotizaciones_dolar_externas import (
    CotizacionDiaria,
)
from src.shared.domain.errors import ExternalServiceError

_logger = logging.getLogger(__name__)

_URL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial"
_TIMEOUT_SECONDS = 30.0


class HttpxArgentinaDatosCotizacionesClient:
    async def fetch_serie_oficial(self) -> list[CotizacionDiaria]:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.get(_URL)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            _logger.error("Fallo consultando cotizaciones en argentinadatos", exc_info=exc)
            raise ExternalServiceError(
                "No se pudo obtener la serie de cotizaciones de argentinadatos"
            ) from exc
        return _parse(payload)


def _parse(payload: object) -> list[CotizacionDiaria]:
    if not isinstance(payload, list):
        raise ExternalServiceError("Respuesta inesperada de argentinadatos (no es una lista)")
    serie: list[CotizacionDiaria] = []
    for item in payload:
        try:
            serie.append(
                CotizacionDiaria(
                    fecha=date.fromisoformat(item["fecha"]),
                    compra=float(item["compra"]),
                    venta=float(item["venta"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            _logger.warning(
                "Cotización inválida en la respuesta de argentinadatos, se ignora",
                extra={"item": item},
                exc_info=exc,
            )
    return serie
