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
from src.modules.contadores.domain.services.cliente_matcher import normalizar_nombre
from src.modules.contadores.domain.services.periodos_facturacion import estado_de_periodo

_MIN_LARGO_NOMBRE = 5


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
        mapa_por_cliente = await self._build_operadores(hoy)
        anotados = [
            AnexoPendienteConEstado(
                anexo=a,
                estado=estado_de_periodo(a.periodo, hoy=hoy),
                operador=_buscar_operador(a.grupo, mapa_por_cliente),
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

    async def _build_operadores(self, hoy: date) -> dict[str, OperadorAsignado]:
        if self._operador_mapa is None:
            return {}
        return await self._operador_mapa.build_por_cliente(hoy=hoy)


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


def _buscar_operador(
    grupo: str | None,
    mapa_norm: dict[str, OperadorAsignado],
) -> OperadorAsignado | None:
    """Cruza el grupo económico del anexo contra nombres normalizados de
    clientes del calendario. Exacto primero, contención única si no hay exacto
    (misma lógica que `match_clientes`/`_match_por_contencion`)."""
    if not grupo or not mapa_norm:
        return None
    norm = normalizar_nombre(grupo)
    if norm in mapa_norm:
        return mapa_norm[norm]
    if len(norm) < _MIN_LARGO_NOMBRE:
        return None
    candidatos = [op for key, op in mapa_norm.items() if norm in key or key in norm]
    return candidatos[0] if len(candidatos) == 1 else None
