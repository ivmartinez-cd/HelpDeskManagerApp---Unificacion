"""Adapter pyodbc del puerto CalendarPort: eventos de facturación desde la
base de Gestión en ORION, en vez del scraping de la web (ADR-047). Arma cada
`CalendarEvent` con el mismo formato que devolvía la web, para que la copia
local y la UI no cambien."""

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.infrastructure.siges.gestion_calendario_query import (
    GESTION_CALENDARIO_FACTURACION_SQL,
)
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner

_ZONA_GESTION = ZoneInfo("America/Argentina/Buenos_Aires")
# Color que la web le daba a los eventos de un operador sin color propio
# (`usuario.color_calendario_planificacion` NULL, caso vipaez, 2026-10-09).
_COLOR_SIN_ASIGNAR = "#FACC2E"


class PyodbcGestionCalendarioGateway:
    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner

    async def get_events(self, start_date: str, end_date: str) -> list[CalendarEvent]:
        """Eventos de facturación pendientes entre `start_date` y `end_date`
        (ISO, ambos inclusive)."""
        hasta = date.fromisoformat(end_date) + timedelta(days=1)
        rows = await self._runner.fetch_all(
            GESTION_CALENDARIO_FACTURACION_SQL,
            (date.fromisoformat(start_date), hasta),
            gateway="gestion_calendario",
            log_message="Fallo la consulta del calendario de facturación contra Gestion/ORION",
            log_extra={"start_date": start_date, "end_date": end_date},
        )
        return [_to_event(row) for row in rows]


def _to_event(row: Any) -> CalendarEvent:
    color = row.color or _COLOR_SIN_ASIGNAR
    return CalendarEvent(
        id=str(row.id),
        title=f"(Facturación) {row.titulo}",
        start=_inicio(row.fecha),
        operador_id=row.username,
        all_day=True,
        background_color=color,
        border_color=color,
        type="E",
        tittle_tooltip=row.titulo,
        content_tooltip=row.descripcion,
        string_tipo_evento="Facturación",
        cliente=row.titulo,
    )


def _inicio(fecha: datetime) -> str:
    """Mismo formato que la web: `2026-10-09T00:00:00-03:00`."""
    return fecha.replace(tzinfo=_ZONA_GESTION).isoformat()
