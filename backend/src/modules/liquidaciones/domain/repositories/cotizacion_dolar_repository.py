"""Puerto de persistencia de `cotizaciones_dolar` — un registro por período
(YYYY-MM), dólar oficial. Ver `SincronizarCotizacionesDolar`."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CotizacionDolar:
    periodo: str
    compra: float
    venta: float
    fecha_cotizacion: date
    fuente: str
    updated_at: datetime


class CotizacionDolarRepository(Protocol):
    async def get_by_periodo(self, periodo: str) -> CotizacionDolar | None: ...

    async def upsert(
        self,
        periodo: str,
        compra: float,
        venta: float,
        fecha_cotizacion: date,
        fuente: str,
    ) -> None:
        """Reemplaza el registro del período si ya existe (mismo criterio que
        el resto del módulo: el mes en curso se pisa en cada corrida del job
        hasta que cierra)."""
        ...
