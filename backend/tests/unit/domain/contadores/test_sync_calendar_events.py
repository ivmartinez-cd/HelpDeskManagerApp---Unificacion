from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.sync_calendar_events import (
    SyncCalendarEventsUseCase,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador

_IDENTIDADES = [
    Operador(id="mjvela", nombre="Maria Jose Vela", color="#FACC2E"),
    Operador(id="vipaez", nombre="Victor Paez", color="#888200"),
]


def _event(event_id: str, operador: str | None, color: str | None = "#FACC2E") -> CalendarEvent:
    return CalendarEvent(
        id=event_id,
        title="(Facturación) X",
        start="2026-08-01T00:00:00-03:00",
        operador_id=operador,
        background_color=color,
    )


def _make_calendar_port(events: list[CalendarEvent]) -> AsyncMock:
    port = AsyncMock()
    port.get_events.return_value = events
    return port


def _make_operador_catalog(identidades: list[Operador]) -> AsyncMock:
    catalog = AsyncMock()
    catalog.find_by_logins.return_value = identidades
    return catalog


@pytest.mark.asyncio
async def test_sync_hace_un_solo_pedido_y_agrupa_por_operador_del_evento() -> None:
    events = [
        _event("1", "mjvela", "#FACC2E"),
        _event("2", "mjvela", "#FACC2E"),
        _event("3", "mjvela", "#BC2FFE"),
        _event("4", "vipaez", "#66B3FF"),
    ]
    port = _make_calendar_port(events)
    catalog = _make_operador_catalog(_IDENTIDADES)
    repo = AsyncMock()

    result = await SyncCalendarEventsUseCase(port, catalog, repo).execute(
        start_date="2026-08-01", end_date="2026-08-31"
    )

    port.get_events.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", solo_facturacion=True
    )
    catalog.find_by_logins.assert_awaited_once_with(["mjvela", "vipaez"])
    assert result.operadores_count == 2
    assert result.events_count == 4
    repo.replace_events_in_range.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", events=events
    )


@pytest.mark.asyncio
async def test_sync_nombre_por_siges_y_color_dominante_de_los_eventos() -> None:
    """El nombre sale de UsuariosWeb, pero el color sale de los eventos:
    UsuariosWeb.color está desactualizado/duplicado (caso real ltorres),
    mientras que el color de los eventos es el que la gente ve en Gestión."""
    events = [
        # mjvela: dominante #FACC2E (2 a 1), aunque UsuariosWeb diga lo mismo
        _event("1", "mjvela", "#FACC2E"),
        _event("2", "mjvela", "#FACC2E"),
        _event("3", "mjvela", "#BC2FFE"),
        # vipaez: los eventos (#66B3FF) pisan el color viejo de UsuariosWeb (#888200)
        _event("4", "vipaez", "#66B3FF"),
        # sin color en los eventos ni identidad: queda username y color None
        _event("5", "desconocido", None),
    ]
    port = _make_calendar_port(events)
    catalog = _make_operador_catalog(_IDENTIDADES)
    repo = AsyncMock()

    await SyncCalendarEventsUseCase(port, catalog, repo).execute(
        start_date="2026-08-01", end_date="2026-08-31"
    )

    (call,) = repo.replace_operadores.await_args_list
    por_id = {op.id: op for op in call.args[0]}
    assert por_id["mjvela"].nombre == "Maria Jose Vela"
    assert por_id["mjvela"].color == "#FACC2E"
    assert por_id["vipaez"].nombre == "Victor Paez"
    assert por_id["vipaez"].color == "#66B3FF"
    # Sin identidad resuelta en Siges, el username queda como nombre visible.
    assert por_id["desconocido"].nombre == "desconocido"
    assert por_id["desconocido"].color is None
    repo.prune_operadores_not_in.assert_awaited_once_with(["desconocido", "mjvela", "vipaez"])


@pytest.mark.asyncio
async def test_sync_sin_color_en_eventos_cae_a_usuariosweb() -> None:
    events = [_event("1", "vipaez", None)]
    port = _make_calendar_port(events)
    catalog = _make_operador_catalog(_IDENTIDADES)
    repo = AsyncMock()

    await SyncCalendarEventsUseCase(port, catalog, repo).execute(
        start_date="2026-08-01", end_date="2026-08-31"
    )

    (call,) = repo.replace_operadores.await_args_list
    por_id = {op.id: op for op in call.args[0]}
    assert por_id["vipaez"].color == "#888200"


@pytest.mark.asyncio
async def test_sync_descarta_y_loguea_eventos_sin_operador(
    caplog: pytest.LogCaptureFixture,
) -> None:
    events = [_event("1", "mjvela"), _event("2", None)]
    port = _make_calendar_port(events)
    catalog = _make_operador_catalog(_IDENTIDADES)
    repo = AsyncMock()

    with caplog.at_level("WARNING"):
        result = await SyncCalendarEventsUseCase(port, catalog, repo).execute(
            start_date="2026-08-01", end_date="2026-08-31"
        )

    assert result.events_count == 1
    assert "sin operador" in caplog.text
    repo.replace_events_in_range.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", events=[events[0]]
    )
