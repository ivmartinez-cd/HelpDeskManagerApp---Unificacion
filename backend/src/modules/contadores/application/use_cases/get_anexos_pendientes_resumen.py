"""KPIs del reporte de cierre de contadores: cuántos anexos quedaron con el
período abierto y cuánta plata (USD calculados por los procesos) está
esperando el cierre. Deriva del mismo snapshot cacheado que el listado."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from src.modules.contadores.domain.ports.anexos_pendientes_port import AnexosPendientesPort
from src.modules.contadores.domain.services.periodos_facturacion import (
    estado_de_periodo,
    periodo_anterior,
    periodo_de,
)


@dataclass(frozen=True)
class AnexosPendientesResumen:
    total: int
    en_proceso: int
    demorados: int
    importe_usd_total: Decimal
    # Período considerado EN PROCESO (el mes anterior al en curso) — la UI lo
    # muestra como referencia del reporte.
    periodo_referencia: str
    consultado_en: datetime


class GetAnexosPendientesResumenUseCase:
    def __init__(self, port: AnexosPendientesPort) -> None:
        self._port = port

    async def execute(self, *, hoy: date | None = None) -> AnexosPendientesResumen:
        snapshot = await self._port.list_anexos()
        hoy = hoy or datetime.now(UTC).date()
        estados = [estado_de_periodo(a.periodo, hoy=hoy) for a in snapshot.anexos]
        return AnexosPendientesResumen(
            total=len(snapshot.anexos),
            en_proceso=sum(1 for e in estados if e == "en_proceso"),
            demorados=sum(1 for e in estados if e == "demorado"),
            importe_usd_total=sum(
                (a.importe_usd for a in snapshot.anexos), start=Decimal(0)
            ),
            periodo_referencia=periodo_anterior(periodo_de(hoy)),
            consultado_en=snapshot.consultado_en,
        )
