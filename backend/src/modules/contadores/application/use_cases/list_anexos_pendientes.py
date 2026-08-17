"""Listado del reporte de cierre de contadores (anexos de Impresión con
período abierto): anota el estado EN PROCESO/DEMORADO y el operador asignado
al cliente (vía calendario + cruce con Siges), filtra/busca en memoria sobre
el snapshot cacheado del puerto. El orden ya viene fijo del SQL (período más
viejo primero, después grupo y anexo) — es un reporte para imprimir, no una
tabla explorable."""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from src.modules.contadores.application.dtos.anexo_pendiente_con_estado import (
    AnexoPendienteConEstado,
)
from src.modules.contadores.application.dtos.equipo_sin_real_anotado import OperadorAsignado
from src.modules.contadores.application.dtos.list_anexos_pendientes_request import (
    ListAnexosPendientesRequest,
)
from src.modules.contadores.application.use_cases.operador_por_empresa import (
    MapaOperadorPorEmpresa,
)
from src.modules.contadores.domain.ports.anexos_pendientes_port import AnexosPendientesPort
from src.modules.contadores.domain.services.periodos_facturacion import estado_de_periodo


@dataclass(frozen=True)
class ListAnexosPendientesResult:
    anexos: list[AnexoPendienteConEstado]
    consultado_en: datetime


class ListAnexosPendientesUseCase:
    def __init__(
        self,
        port: AnexosPendientesPort,
        operador_mapa: MapaOperadorPorEmpresa | None = None,
    ) -> None:
        self._port = port
        self._operador_mapa = operador_mapa

    async def execute(
        self, request: ListAnexosPendientesRequest, *, hoy: date | None = None
    ) -> ListAnexosPendientesResult:
        snapshot = await self._port.list_anexos(force_refresh=request.force_refresh)
        hoy = hoy or datetime.now(UTC).date()
        operadores = await self._build_operadores(hoy)
        anotados = [
            AnexoPendienteConEstado(
                anexo=a,
                estado=estado_de_periodo(a.periodo, hoy=hoy),
                operador=operadores.get(a.id_empresa_admin) if a.id_empresa_admin else None,
            )
            for a in snapshot.anexos
        ]
        if request.estado != "todos":
            anotados = [a for a in anotados if a.estado == request.estado]
        if request.search:
            anotados = _filtrar(anotados, request.search)
        return ListAnexosPendientesResult(
            anexos=anotados, consultado_en=snapshot.consultado_en
        )

    async def _build_operadores(self, hoy: date) -> dict[int, OperadorAsignado]:
        if self._operador_mapa is None:
            return {}
        return await self._operador_mapa.build(hoy=hoy)


def _filtrar(
    anotados: list[AnexoPendienteConEstado], search: str
) -> list[AnexoPendienteConEstado]:
    needle = search.casefold()
    return [a for a in anotados if _matchea(a, needle)]


def _matchea(anotado: AnexoPendienteConEstado, needle: str) -> bool:
    anexo = anotado.anexo
    operador_nombre = anotado.operador.nombre if anotado.operador else None
    campos = (anexo.grupo, anexo.contrato, anexo.anexo, anexo.vendedor, anexo.periodo,
              operador_nombre)
    return any(needle in campo.casefold() for campo in campos if campo)
