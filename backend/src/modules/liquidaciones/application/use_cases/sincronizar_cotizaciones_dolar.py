"""Caso de uso del job `liquidaciones_sync_cotizaciones` — dólar oficial por
período (YYYY-MM) desde 2026-01 en adelante, para el switch ARS/USD del
detalle de liquidación. Meses cerrados: valor definitivo de ArgentinaDatos
(cierre de mes). Mes en curso: valor de hoy de dolarapi.com, se pisa en cada
corrida hasta que el mes cierra y ArgentinaDatos publica el dato final."""

from dataclasses import dataclass
from datetime import date

from src.modules.liquidaciones.domain.repositories.cotizacion_dolar_repository import (
    CotizacionDolarRepository,
)
from src.modules.liquidaciones.domain.repositories.cotizaciones_dolar_externas import (
    CotizacionesHistoricasProvider,
    CotizacionHoyProvider,
)
from src.modules.liquidaciones.domain.services.cierres_de_mes_cotizacion import (
    planificar_cierres_de_mes,
)

PERIODO_INICIO = "2026-01"


@dataclass(frozen=True)
class SincronizarCotizacionesDolarPorts:
    cotizaciones: CotizacionDolarRepository
    historicas: CotizacionesHistoricasProvider
    hoy: CotizacionHoyProvider


@dataclass(frozen=True)
class SincronizarCotizacionesDolarResultado:
    actualizados: int


class SincronizarCotizacionesDolar:
    def __init__(self, ports: SincronizarCotizacionesDolarPorts) -> None:
        self._ports = ports

    async def execute(self) -> SincronizarCotizacionesDolarResultado:
        hoy = date.today()
        periodo_actual = f"{hoy.year:04d}-{hoy.month:02d}"

        actualizados = await self._sync_meses_cerrados(periodo_actual)
        if periodo_actual >= PERIODO_INICIO:
            await self._sync_mes_actual(periodo_actual)
            actualizados += 1
        return SincronizarCotizacionesDolarResultado(actualizados=actualizados)

    async def _sync_meses_cerrados(self, periodo_actual: str) -> int:
        serie = await self._ports.historicas.fetch_serie_oficial()
        cierres = planificar_cierres_de_mes(serie, PERIODO_INICIO, periodo_actual)
        for periodo, dia in cierres.items():
            await self._ports.cotizaciones.upsert(
                periodo, dia.compra, dia.venta, dia.fecha, "argentinadatos"
            )
        return len(cierres)

    async def _sync_mes_actual(self, periodo_actual: str) -> None:
        dia = await self._ports.hoy.fetch_oficial_hoy()
        await self._ports.cotizaciones.upsert(
            periodo_actual, dia.compra, dia.venta, dia.fecha, "dolarapi"
        )
