"""Mapa `ID_Empresa` de Siges → operador asignado, para anotar el análisis de
equipos sin contador real. La cadena es la inversa del cruce de la card de
Inicio (`get_resumen_clientes_operador`): eventos del calendario local
(cliente de Gestión + operador) → `match_clientes` (alias manual + nombre
normalizado) → `ID_Empresa`. La "asignación vigente" de un cliente con varios
eventos es la del evento más cercano a hoy, prefiriendo los futuros (la
planificación hacia adelante refleja la asignación actual)."""

import logging
from datetime import date, timedelta

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import OperadorAsignado
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
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

# ±45 días: cubre la planificación del mes en curso y el que viene, cómodo
# dentro de la ventana de sync del calendario (±90 — ver calendario_router).
_VENTANA_DIAS = 45


class MapaOperadorPorEmpresa:
    def __init__(
        self,
        calendar: CalendarEventRepository,
        alias: ClienteSigesMapRepository,
        parque: ParqueClientePort,
    ) -> None:
        self._calendar = calendar
        self._alias = alias
        self._parque = parque

    async def build_por_cliente(self, *, hoy: date) -> dict[str, OperadorAsignado]:
        """Nombre normalizado de Gestión → operador, para cruce por nombre
        cuando no hay ID de Siges confiable (ej. anexos-pendientes vs
        ID_EmpresaAdmin del contrato). Degrada a vacío si el cruce falla."""
        from src.modules.contadores.domain.services.cliente_matcher import normalizar_nombre

        try:
            raw = await self._operador_por_cliente(hoy)
        except ExternalServiceError as exc:
            logger.warning(
                "Sin cruce cliente→operador por nombre; el listado va sin operador",
                exc_info=exc,
            )
            return {}
        return {normalizar_nombre(k): v for k, v in raw.items()}

    async def build(self, *, hoy: date) -> dict[int, OperadorAsignado]:
        """Vacío si el cruce no se puede armar (Siges caído): el listado
        degrada a mostrarse sin operador, no falla."""
        try:
            operador_por_cliente = await self._operador_por_cliente(hoy)
            if not operador_por_cliente:
                return {}
            matches = match_clientes(
                sorted(operador_por_cliente),
                await self._parque.list_empresas_activas(),
                await self._alias.list_all(),
            )
        except ExternalServiceError as exc:
            logger.warning(
                "Sin cruce cliente→operador desde Siges; el listado de equipos "
                "sin real va sin columna de operador",
                exc_info=exc,
            )
            return {}
        return self._invertir(matches, operador_por_cliente)

    async def _operador_por_cliente(self, hoy: date) -> dict[str, OperadorAsignado]:
        desde = (hoy - timedelta(days=_VENTANA_DIAS)).isoformat()
        hasta = (hoy + timedelta(days=_VENTANA_DIAS)).isoformat()
        events = await self._calendar.list_events(
            start_date=desde, end_date=hasta, operador_id=None
        )
        vigente_por_cliente: dict[str, CalendarEvent] = {}
        for event in events:
            if not event.cliente or not event.operador_id:
                continue
            actual = vigente_por_cliente.get(event.cliente)
            if actual is None or _prioridad(event, hoy) < _prioridad(actual, hoy):
                vigente_por_cliente[event.cliente] = event
        return await self._resolver_nombres(vigente_por_cliente)

    async def _resolver_nombres(
        self, vigente_por_cliente: dict[str, CalendarEvent]
    ) -> dict[str, OperadorAsignado]:
        operadores = {o.id: o for o in await self._calendar.list_operadores()}
        resultado: dict[str, OperadorAsignado] = {}
        for cliente, event in vigente_por_cliente.items():
            operador = operadores.get(event.operador_id or "")
            resultado[cliente] = OperadorAsignado(
                nombre=operador.nombre if operador else (event.operador_id or ""),
                color=operador.color if operador else None,
            )
        return resultado

    @staticmethod
    def _invertir(
        matches: dict[str, list[int]],
        operador_por_cliente: dict[str, OperadorAsignado],
    ) -> dict[int, OperadorAsignado]:
        # Si dos clientes de Gestión mapean a la misma empresa con distinto
        # operador (raro: alias regionales), gana el primero en orden
        # alfabético de cliente — determinístico, y el caso no amerita más.
        resultado: dict[int, OperadorAsignado] = {}
        for cliente in sorted(matches):
            for id_empresa in matches[cliente]:
                resultado.setdefault(id_empresa, operador_por_cliente[cliente])
        return resultado


def _prioridad(event: CalendarEvent, hoy: date) -> tuple[int, int]:
    """Menor = más representativo de la asignación actual: primero el evento
    futuro más próximo, después el pasado más reciente."""
    fecha = date.fromisoformat(event.start[:10])
    delta = abs((fecha - hoy).days)
    return (0, delta) if fecha >= hoy else (1, delta)
