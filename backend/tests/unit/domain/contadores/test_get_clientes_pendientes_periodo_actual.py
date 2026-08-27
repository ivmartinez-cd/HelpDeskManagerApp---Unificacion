from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.application.use_cases.get_clientes_pendientes_periodo_actual import (
    GetClientesPendientesPeriodoActualUseCase,
)
from src.modules.contadores.application.use_cases.get_pending_clients import (
    GetPendingClientsUseCase,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador

_HOY = date(2026, 8, 27)  # en arrastre: período 202608, 20/8 al 20/9
_OPERADOR_ID = "749"
_FULL_NAME = "Ivan Martinez"


def _event(
    event_id: str, start_date: date, operador_id: str = _OPERADOR_ID, cliente: str | None = None
) -> CalendarEvent:
    return CalendarEvent(
        id=event_id,
        title="[Facturación]: X",
        start=f"{start_date.isoformat()}T00:00:00-03:00",
        cliente=cliente or f"Cliente-{event_id}",
        operador_id=operador_id,
    )


def _mock_repo(events: list[CalendarEvent] | None = None) -> AsyncMock:
    mock = AsyncMock()
    mock.list_events.return_value = events or []
    mock.list_operadores.return_value = [Operador(id=_OPERADOR_ID, nombre=_FULL_NAME)]
    mock.find_operador_by_nombre.return_value = Operador(id=_OPERADOR_ID, nombre=_FULL_NAME)
    return mock


def _mock_overrides() -> AsyncMock:
    mock = AsyncMock()
    mock.list_activos.return_value = []
    mock.list_activos_por_ausente.return_value = []
    mock.list_activos_por_reemplazante.return_value = []
    return mock


def _use_case(repo_mock: AsyncMock) -> GetClientesPendientesPeriodoActualUseCase:
    overrides = _mock_overrides()
    pending = GetPendingClientsUseCase(GetCalendarEventsUseCase(repo_mock, overrides), repo_mock)
    return GetClientesPendientesPeriodoActualUseCase(pending)


@pytest.mark.asyncio
async def test_incluye_eventos_todavia_no_vencidos() -> None:
    """A diferencia del backlog puro, un evento con fecha FUTURA (todavía no
    llegó su día) dentro del período en curso también cuenta como pendiente."""
    futuro = _HOY + timedelta(days=5)
    repo = _mock_repo([_event("e1", futuro)])
    uc = _use_case(repo)

    result = await uc.execute(is_superadmin=False, full_name=_FULL_NAME, today=_HOY)

    assert [a.event.id for a in result] == ["e1"]


@pytest.mark.asyncio
async def test_pide_la_ventana_del_periodo_en_curso_no_90_dias() -> None:
    repo = _mock_repo([])
    uc = _use_case(repo)

    await uc.execute(is_superadmin=False, full_name=_FULL_NAME, today=_HOY)

    call_kwargs = repo.list_events.call_args.kwargs
    assert call_kwargs["start_date"] == "2026-08-20"
    assert call_kwargs["end_date"] == "2026-09-20"


@pytest.mark.asyncio
async def test_eventos_fuera_de_la_ventana_del_periodo_no_aparecen() -> None:
    del_periodo = _event("dentro", _HOY + timedelta(days=1))
    del_proximo_periodo = _event("afuera", date(2026, 9, 21))
    repo = _mock_repo([del_periodo, del_proximo_periodo])
    uc = _use_case(repo)

    async def list_events(start_date: str, end_date: str, operador_id: str | None):
        eventos = [del_periodo, del_proximo_periodo]
        return [e for e in eventos if start_date <= e.start[:10] <= end_date]

    repo.list_events.side_effect = list_events

    result = await uc.execute(is_superadmin=False, full_name=_FULL_NAME, today=_HOY)

    assert [a.event.id for a in result] == ["dentro"]


@pytest.mark.asyncio
async def test_mismo_cliente_con_dos_eventos_queda_una_sola_fila() -> None:
    """El primero por fecha (GetPendingClientsUseCase ya ordena ascendente)."""
    primero = _event("e1", _HOY, cliente="Cliente-repetido")
    segundo = _event("e2", _HOY + timedelta(days=2), cliente="Cliente-repetido")
    repo = _mock_repo([primero, segundo])
    uc = _use_case(repo)

    result = await uc.execute(is_superadmin=False, full_name=_FULL_NAME, today=_HOY)

    assert [a.event.id for a in result] == ["e1"]
