"""Listado del reporte de cierre de contadores (anexos de Impresión con
período abierto): anota el estado EN PROCESO/DEMORADO según el calendario y
filtra/busca en memoria sobre el snapshot cacheado del puerto. El orden ya
viene fijo del SQL (período más viejo primero, después grupo y anexo) — es
un reporte para imprimir, no una tabla explorable."""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from src.modules.contadores.application.dtos.anexo_pendiente_con_estado import (
    AnexoPendienteConEstado,
)
from src.modules.contadores.application.dtos.list_anexos_pendientes_request import (
    ListAnexosPendientesRequest,
)
from src.modules.contadores.domain.entities.anexo_pendiente import AnexoPendiente
from src.modules.contadores.domain.ports.anexos_pendientes_port import AnexosPendientesPort
from src.modules.contadores.domain.services.periodos_facturacion import estado_de_periodo


@dataclass(frozen=True)
class ListAnexosPendientesResult:
    anexos: list[AnexoPendienteConEstado]
    consultado_en: datetime


class ListAnexosPendientesUseCase:
    def __init__(self, port: AnexosPendientesPort) -> None:
        self._port = port

    async def execute(
        self, request: ListAnexosPendientesRequest, *, hoy: date | None = None
    ) -> ListAnexosPendientesResult:
        snapshot = await self._port.list_anexos(force_refresh=request.force_refresh)
        hoy = hoy or datetime.now(UTC).date()
        anotados = [
            AnexoPendienteConEstado(anexo=a, estado=estado_de_periodo(a.periodo, hoy=hoy))
            for a in snapshot.anexos
        ]
        if request.estado != "todos":
            anotados = [a for a in anotados if a.estado == request.estado]
        if request.search:
            anotados = _filtrar(anotados, request.search)
        return ListAnexosPendientesResult(
            anexos=anotados, consultado_en=snapshot.consultado_en
        )


def _filtrar(
    anotados: list[AnexoPendienteConEstado], search: str
) -> list[AnexoPendienteConEstado]:
    needle = search.casefold()
    return [a for a in anotados if _matchea(a.anexo, needle)]


def _matchea(anexo: AnexoPendiente, needle: str) -> bool:
    campos = (anexo.grupo, anexo.contrato, anexo.anexo, anexo.vendedor, anexo.periodo)
    return any(needle in campo.casefold() for campo in campos if campo)
