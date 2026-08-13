from collections import defaultdict
from datetime import date

from src.modules.contadores.application.dtos.calendar_event_anotado import (
    CalendarEventAnotado,
    CoberturaDeEventoDTO,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.services.operador_efectivo import resolver_override_aplicable


def anotar_eventos(
    events: list[CalendarEvent],
    overrides: list[AsignacionOverride],
    operadores_por_id: dict[str, Operador],
) -> list[CalendarEventAnotado]:
    """Anota cada evento con el override que le aplica (si hay uno), resuelto
    con la fecha propia del evento — los eventos nunca se mueven ni se
    ocultan, solo se marcan (ver ADR-013 fase 2 y el principio del handoff:
    "el operador real nunca desaparece")."""
    por_ausente: dict[str, list[AsignacionOverride]] = defaultdict(list)
    for override in overrides:
        por_ausente[override.operador_ausente_id].append(override)
    return [
        _anotar_evento(event, por_ausente.get(event.operador_id or "", []), operadores_por_id)
        for event in events
    ]


def _anotar_evento(
    event: CalendarEvent,
    reglas: list[AsignacionOverride],
    operadores_por_id: dict[str, Operador],
) -> CalendarEventAnotado:
    override = resolver_override_aplicable(
        event.operador_id, event.cliente, _event_date(event), reglas
    )
    if override is None:
        return CalendarEventAnotado(event=event, cobertura=None)
    return CalendarEventAnotado(
        event=event, cobertura=_build_cobertura(override, operadores_por_id)
    )


def _build_cobertura(
    override: AsignacionOverride, operadores_por_id: dict[str, Operador]
) -> CoberturaDeEventoDTO:
    ausente = operadores_por_id.get(override.operador_ausente_id)
    reemplazante = operadores_por_id.get(override.operador_reemplazante_id)
    return CoberturaDeEventoDTO(
        override_id=override.id,
        operador_ausente_id=override.operador_ausente_id,
        operador_ausente_nombre=ausente.nombre if ausente else None,
        operador_reemplazante_id=override.operador_reemplazante_id,
        operador_reemplazante_nombre=reemplazante.nombre if reemplazante else None,
        operador_reemplazante_color=reemplazante.color if reemplazante else None,
        vigente_desde=override.vigente_desde,
        vigente_hasta=override.vigente_hasta,
        alcance_total=override.alcance == "TOTAL",
    )


def _event_date(event: CalendarEvent) -> date:
    return date.fromisoformat(event.start[:10])
