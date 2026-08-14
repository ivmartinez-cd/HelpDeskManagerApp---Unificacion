"""Resumen para la card de Inicio: la cartera de clientes de cada operador y
cuántas impresoras suman esos clientes. La cartera se cuenta mirando el
calendario local (copia de Gestión) **hacia adelante** por toda la ventana
sincronizada: Gestión borra los eventos ya realizados, así que el mes en
curso subcuenta cada vez más a medida que avanza; como toda cuenta se factura
al menos una vez por mes, la ventana futura contiene la cartera completa
(verificado 2026-08-14 contra la planilla de cuentas por operador de la TL:
75/74/62/52 vs 74/72/62/53). Las impresoras salen del cruce por nombre contra
Siges (ver cliente_matcher) — los que no cruzan se informan aparte en
`sin_cruce`, no se inventa un cero. Si Siges no responde, la card degrada a
mostrar solo clientes (impresoras=None)."""

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.contadores.application.dtos.resumen_clientes_operador import (
    OperadorClientesDTO,
    ResumenClientesOperadorDTO,
)
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.ports.parque_cliente_port import ParqueClientePort
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)
from src.modules.contadores.domain.repositories.cliente_siges_map_repository import (
    ClienteSigesMapRepository,
)
from src.modules.contadores.domain.services.cliente_matcher import match_clientes
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetResumenClientesOperadorDependencies:
    calendar: CalendarEventRepository
    alias: ClienteSigesMapRepository
    parque: ParqueClientePort | None
    """`None` (o caído) degrada a clientes sin conteo de impresoras."""


class GetResumenClientesOperador:
    def __init__(self, deps: GetResumenClientesOperadorDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        *,
        hoy: date,
        dias_ventana: int,
        exclude_operador_ids: frozenset[str] = frozenset(),
    ) -> ResumenClientesOperadorDTO:
        desde = hoy
        hasta = hoy + timedelta(days=dias_ventana)
        clientes_por_operador = await self._clientes_por_operador(
            desde, hasta, exclude_operador_ids
        )
        todos = sorted({c for clientes in clientes_por_operador.values() for c in clientes})
        cruce = await self._cruce_con_impresoras(todos)
        operadores = await self._armar_filas(clientes_por_operador, cruce)
        return ResumenClientesOperadorDTO(
            desde=desde,
            hasta=hasta,
            total_clientes=len(todos),
            total_impresoras=self._total_impresoras(operadores),
            operadores=operadores,
        )

    async def _clientes_por_operador(
        self, desde: date, hasta: date, exclude: frozenset[str]
    ) -> dict[str, set[str]]:
        events = await self._deps.calendar.list_events(
            start_date=desde.isoformat(), end_date=hasta.isoformat(), operador_id=None
        )
        agrupado: dict[str, set[str]] = {}
        for event in events:
            if not event.cliente or not event.operador_id or event.operador_id in exclude:
                continue
            agrupado.setdefault(event.operador_id, set()).add(event.cliente)
        return agrupado

    async def _cruce_con_impresoras(self, clientes: list[str]) -> dict[str, int] | None:
        """`cliente` → impresoras (solo los que cruzaron). None = Siges caído."""
        if self._deps.parque is None or not clientes:
            return None if self._deps.parque is None else {}
        try:
            empresas = await self._deps.parque.list_empresas_activas()
            alias = await self._deps.alias.list_all()
            matches = match_clientes(clientes, empresas, alias)
            ids = sorted({id_ for ids in matches.values() for id_ in ids})
            impresoras = await self._deps.parque.count_impresoras_by_empresa_ids(ids)
        except ExternalServiceError as exc:
            logger.warning(
                "Sin conteo de impresoras por cliente desde Siges; la card degrada a "
                "solo clientes",
                extra={"cantidad_clientes": len(clientes)},
                exc_info=exc,
            )
            return None
        return {
            cliente: sum(impresoras.get(id_, 0) for id_ in ids_cliente)
            for cliente, ids_cliente in matches.items()
            if ids_cliente
        }

    async def _armar_filas(
        self, clientes_por_operador: dict[str, set[str]], cruce: dict[str, int] | None
    ) -> list[OperadorClientesDTO]:
        operadores = {o.id: o for o in await self._deps.calendar.list_operadores()}
        filas = [
            self._fila(operador_id, sorted(clientes), operadores, cruce)
            for operador_id, clientes in clientes_por_operador.items()
        ]
        return sorted(filas, key=lambda f: (-f.clientes, f.operador_nombre))

    def _fila(
        self,
        operador_id: str,
        clientes: list[str],
        operadores: dict[str, Operador],
        cruce: dict[str, int] | None,
    ) -> OperadorClientesDTO:
        operador = operadores.get(operador_id)
        return OperadorClientesDTO(
            operador_id=operador_id,
            operador_nombre=operador.nombre if operador else operador_id,
            operador_color=operador.color if operador else None,
            clientes=len(clientes),
            impresoras=(
                None if cruce is None else sum(cruce[c] for c in clientes if c in cruce)
            ),
            sin_cruce=[] if cruce is None else [c for c in clientes if c not in cruce],
        )

    @staticmethod
    def _total_impresoras(operadores: list[OperadorClientesDTO]) -> int | None:
        if any(f.impresoras is None for f in operadores):
            return None
        return sum(f.impresoras or 0 for f in operadores)
