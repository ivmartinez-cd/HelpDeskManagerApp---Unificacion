from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.sync_calendar_events import (
    SyncCalendarEventsUseCase,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador

_CATALOGO = [
    Operador(id="318", nombre="Maria Jose Vela"),
    Operador(id="1246", nombre="Victor Paez"),
    Operador(id="749", nombre="Ivan Martinez"),
]


def _event(event_id: str, operador: str | None, color: str | None = "#FACC2E") -> CalendarEvent:
    return CalendarEvent(
        id=event_id,
        title="(Facturación) X",
        start="2026-08-01T00:00:00-03:00",
        operador_id=operador,
        background_color=color,
    )


def _make_port(events: list[CalendarEvent]) -> AsyncMock:
    port = AsyncMock()
    port.get_operadores.return_value = _CATALOGO
    port.get_events.return_value = events
    return port


@pytest.mark.asyncio
async def test_sync_hace_un_solo_pedido_y_agrupa_por_operador_del_evento() -> None:
    events = [
        _event("1", "mjvela", "#FACC2E"),
        _event("2", "mjvela", "#FACC2E"),
        _event("3", "mjvela", "#BC2FFE"),
        _event("4", "vipaez", "#66B3FF"),
    ]
    port = _make_port(events)
    repo = AsyncMock()

    result = await SyncCalendarEventsUseCase(port, repo).execute(
        start_date="2026-08-01", end_date="2026-08-31"
    )

    port.get_events.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", solo_facturacion=True
    )
    assert result.operadores_count == 2
    assert result.events_count == 4
    repo.replace_events_in_range.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", events=events
    )


@pytest.mark.asyncio
async def test_sync_resuelve_nombre_de_catalogo_y_color_mas_frecuente() -> None:
    events = [
        _event("1", "mjvela", "#FACC2E"),
        _event("2", "mjvela", "#FACC2E"),
        _event("3", "mjvela", "#BC2FFE"),
        _event("4", "vipaez", "#66B3FF"),
        _event("5", "desconocido", None),
    ]
    repo = AsyncMock()

    await SyncCalendarEventsUseCase(_make_port(events), repo).execute(
        start_date="2026-08-01", end_date="2026-08-31"
    )

    (call,) = repo.replace_operadores.await_args_list
    por_id = {op.id: op for op in call.args[0]}
    assert por_id["mjvela"].nombre == "Maria Jose Vela"
    assert por_id["mjvela"].color == "#FACC2E"
    assert por_id["vipaez"].nombre == "Victor Paez"
    # Sin match único en el catálogo, el username queda como nombre visible.
    assert por_id["desconocido"].nombre == "desconocido"
    assert por_id["desconocido"].color is None
    repo.prune_operadores_not_in.assert_awaited_once_with(["desconocido", "mjvela", "vipaez"])


@pytest.mark.asyncio
async def test_sync_descarta_y_loguea_eventos_sin_operador(
    caplog: pytest.LogCaptureFixture,
) -> None:
    events = [_event("1", "mjvela"), _event("2", None)]
    repo = AsyncMock()

    with caplog.at_level("WARNING"):
        result = await SyncCalendarEventsUseCase(_make_port(events), repo).execute(
            start_date="2026-08-01", end_date="2026-08-31"
        )

    assert result.events_count == 1
    assert "sin operador" in caplog.text
    repo.replace_events_in_range.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", events=[events[0]]
    )
