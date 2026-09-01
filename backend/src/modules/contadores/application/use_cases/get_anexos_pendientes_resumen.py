"""KPIs del reporte de cierre de contadores: cuántos anexos quedaron con el
período abierto y cuánta plata (USD calculados por los procesos) está
esperando el cierre. Deriva del mismo snapshot cacheado que el listado."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from src.modules.contadores.domain.ports.anexos_pendientes_port import AnexosPendientesPort
from src.modules.contadores.domain.services.ciclo_cierre import hoy_argentina
from src.modules.contadores.domain.services.periodos_facturacion import (
    estado_de_periodo,
    periodo_anterior,
    periodo_de,
)


@dataclass(frozen=True)
class AnexosPendientesResumen:
    # `total`/`en_proceso`/`demorados`/`importe_usd_total` excluyen el mes en
    # curso a propósito — son los KPIs del cierre (regla TL 2026-08-14), no
    # cambian de significado por el filtro MES_EN_CURSO agregado 2026-08-28.
    total: int
    en_proceso: int
    demorados: int
    importe_usd_total: Decimal
    mes_en_curso: int
    # Período considerado EN PROCESO (el mes anterior al en curso) — la UI lo
    # muestra como referencia del reporte.
    periodo_referencia: str
    consultado_en: datetime


class GetAnexosPendientesResumenUseCase:
    def __init__(self, port: AnexosPendientesPort) -> None:
        self._port = port

    async def execute(self, *, hoy: date | None = None) -> AnexosPendientesResumen:
        snapshot = await self._port.list_anexos()
        hoy = hoy or hoy_argentina()
        anotados = [(a, estado_de_periodo(a.periodo, hoy=hoy)) for a in snapshot.anexos]
        pendientes = [(a, e) for a, e in anotados if e != "mes_en_curso"]
        return AnexosPendientesResumen(
            total=len(pendientes),
            en_proceso=sum(1 for _, e in pendientes if e == "en_proceso"),
            demorados=sum(1 for _, e in pendientes if e == "demorado"),
            importe_usd_total=sum((a.importe_usd for a, _ in pendientes), start=Decimal(0)),
            mes_en_curso=sum(1 for _, e in anotados if e == "mes_en_curso"),
            periodo_referencia=periodo_anterior(periodo_de(hoy)),
            consultado_en=snapshot.consultado_en,
        )
