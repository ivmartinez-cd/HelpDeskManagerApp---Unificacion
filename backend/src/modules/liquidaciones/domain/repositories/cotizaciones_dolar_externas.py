"""Puertos de las dos fuentes externas de cotización del dólar oficial usadas
por `SincronizarCotizacionesDolar`: ArgentinaDatos para meses ya cerrados
(serie histórica completa) y dolarapi.com para el mes en curso (solo trae el
valor de hoy)."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CotizacionDiaria:
    fecha: date
    compra: float
    venta: float


class CotizacionesHistoricasProvider(Protocol):
    """Serie histórica completa del dólar oficial (api.argentinadatos.com).
    Levanta ExternalServiceError si el servicio falla."""

    async def fetch_serie_oficial(self) -> list[CotizacionDiaria]: ...


class CotizacionHoyProvider(Protocol):
    """Cotización del dólar oficial vigente hoy (dolarapi.com). Levanta
    ExternalServiceError si el servicio falla."""

    async def fetch_oficial_hoy(self) -> CotizacionDiaria: ...
