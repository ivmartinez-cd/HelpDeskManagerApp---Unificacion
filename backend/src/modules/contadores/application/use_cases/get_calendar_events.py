from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.cobertura_evento_anotador import anotar_eventos
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)


class GetCalendarEventsUseCase:
    """Lee la copia local (sincronizada aparte, ver SyncCalendarEventsUseCase)
    y anota cada evento con su cobertura vigente (ADR-013 fase 2): el evento
    conserva siempre su operador real y la anotación dice quién lo cubre — la
    vista "efectivo/real" la decide el cliente al renderizar, el contrato es
    uno solo. Superadmin ve todos los operadores por default y puede filtrar
    por uno puntual vía `request.operador_id` (filtro por asignación real, es
    una vista administrativa — la anotación viaja igual). El resto ve solo lo
    que matchea su propio full_name contra el catálogo de operadores de
    Gestión: sus eventos propios (incluidos los que otro le cubre, anotados —
    nunca desaparecen de su vista) más los eventos que él cubre por override
    activo. Sin match de operador, no ve eventos, y no puede pedir el
    operador de otra persona vía el filtro."""

    def __init__(
        self, repository: CalendarEventRepository, overrides: AsignacionOverrideRepository
    ) -> None:
        self._repository = repository
        self._overrides = overrides

    async def execute(self, request: GetCalendarEventsRequest) -> list[CalendarEventAnotado]:
        if request.is_superadmin:
            return await self._vista_superadmin(request)
        return await self._vista_operador(request)

    async def _vista_superadmin(
        self, request: GetCalendarEventsRequest
    ) -> list[CalendarEventAnotado]:
        events = await self._repository.list_events(
            start_date=request.start_date,
            end_date=request.end_date,
            operador_id=request.operador_id,
        )
        activos = await self._overrides.list_activos()
        return anotar_eventos(events, activos, await self._operadores_por_id(activos))

    async def _vista_operador(
        self, request: GetCalendarEventsRequest
    ) -> list[CalendarEventAnotado]:
        operador = await self._repository.find_operador_by_nombre(request.full_name)
        if operador is None:
            return []
        propios = await self._repository.list_events(
            start_date=request.start_date, end_date=request.end_date, operador_id=operador.id
        )
        me_cubren = await self._overrides.list_activos_por_ausente(operador.id)
        anotados = anotar_eventos(propios, me_cubren, await self._operadores_por_id(me_cubren))
        anotados += await self._eventos_que_cubro(operador.id, request)
        return _dedupe_by_id(anotados)

    async def _eventos_que_cubro(
        self, operador_id: str, request: GetCalendarEventsRequest
    ) -> list[CalendarEventAnotado]:
        cubro_a = await self._overrides.list_activos_por_reemplazante(operador_id)
        operadores = await self._operadores_por_id(cubro_a)
        cubiertos: list[CalendarEventAnotado] = []
        for ausente_id in {o.operador_ausente_id for o in cubro_a}:
            reglas = [o for o in cubro_a if o.operador_ausente_id == ausente_id]
            eventos = await self._repository.list_events(
                start_date=request.start_date, end_date=request.end_date, operador_id=ausente_id
            )
            cubiertos += [
                a
                for a in anotar_eventos(eventos, reglas, operadores)
                if a.cobertura is not None
                and a.cobertura.operador_reemplazante_id == operador_id
            ]
        return cubiertos

    async def _operadores_por_id(
        self, overrides: list[AsignacionOverride]
    ) -> dict[str, Operador]:
        """El catálogo solo hace falta para resolver nombres/colores de la
        anotación — sin overrides activos no se consulta."""
        if not overrides:
            return {}
        return {o.id: o for o in await self._repository.list_operadores()}


def _dedupe_by_id(anotados: list[CalendarEventAnotado]) -> list[CalendarEventAnotado]:
    seen: set[str] = set()
    deduped: list[CalendarEventAnotado] = []
    for anotado in anotados:
        if anotado.event.id in seen:
            continue
        seen.add(anotado.event.id)
        deduped.append(anotado)
    return deduped
