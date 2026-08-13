import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent


@dataclass(slots=True, frozen=True)
class CoberturaDeEventoDTO:
    """Anotación de cobertura de un evento del Calendario (ADR-013, fase 2):
    el evento conserva su asignación real (`CalendarEvent.operador_id`) y esta
    anotación dice quién lo cubre efectivamente — la vista "efectivo/real" es
    una decisión de render del cliente, nunca dos contratos distintos."""

    override_id: uuid.UUID
    operador_ausente_id: str
    operador_ausente_nombre: str | None
    operador_reemplazante_id: str
    operador_reemplazante_nombre: str | None
    operador_reemplazante_color: str | None
    vigente_desde: date
    vigente_hasta: date
    alcance_total: bool


@dataclass(slots=True, frozen=True)
class CalendarEventAnotado:
    event: CalendarEvent
    cobertura: CoberturaDeEventoDTO | None
