import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.application.use_cases.get_pending_clients import (
    GetPendingClientsUseCase,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador

_TODAY = date(2026, 8, 14)
_OPERADOR_ID = "749"
_FULL_NAME = "Ivan Martinez"


def _event(event_id: str, start_date: date, operador_id: str = _OPERADOR_ID) -> CalendarEvent:
    return CalendarEvent(
        id=event_id,
        title="[Facturación]: X",
        start=f"{start_date.isoformat()}T00:00:00-03:00",
        cliente=f"Cliente-{event_id}",
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


def _use_case(
    events: list[CalendarEvent] | None = None,
    overrides_mock: AsyncMock | None = None,
    repo_mock: AsyncMock | None = None,
) -> GetPendingClientsUseCase:
    repo = repo_mock or _mock_repo(events)
    overrides = overrides_mock or _mock_overrides()
    return GetPendingClientsUseCase(GetCalendarEventsUseCase(repo, overrides), repo)


@pytest.mark.asyncio
async def test_sin_pendientes_devuelve_vacio() -> None:
    uc = _use_case(events=[])
    result = await uc.execute(
        is_superadmin=False, full_name=_FULL_NAME, today=_TODAY, cutoff_days=30
    )
    assert result == []


@pytest.mark.asyncio
async def test_pendiente_de_un_dia_aparece() -> None:
    ayer = _TODAY - timedelta(days=1)
    uc = _use_case(events=[_event("e1", ayer)])
    result = await uc.execute(
        is_superadmin=False, full_name=_FULL_NAME, today=_TODAY, cutoff_days=30
    )
    assert len(result) == 1
    assert result[0].event.id == "e1"
    assert result[0].event.start.startswith(ayer.isoformat())


@pytest.mark.asyncio
async def test_rango_excluye_hoy() -> None:
    """list_events debe recibir end_date = hoy-1, nunca hoy mismo."""
    repo = _mock_repo([])
    uc = _use_case(repo_mock=repo)
    await uc.execute(is_superadmin=False, full_name=_FULL_NAME, today=_TODAY, cutoff_days=30)

    call_kwargs = repo.list_events.call_args.kwargs
    assert call_kwargs["end_date"] == "2026-08-13"


@pytest.mark.asyncio
async def test_corte_de_30_dias() -> None:
    """list_events debe recibir start_date = hoy-30; eventos de hoy-31 nunca se piden."""
    repo = _mock_repo([])
    uc = _use_case(repo_mock=repo)
    await uc.execute(is_superadmin=False, full_name=_FULL_NAME, today=_TODAY, cutoff_days=30)

    call_kwargs = repo.list_events.call_args.kwargs
    assert call_kwargs["start_date"] == "2026-07-15"


@pytest.mark.asyncio
async def test_ordena_del_mas_viejo_al_mas_nuevo() -> None:
    """Los eventos deben llegar ordenados ascendente por start
    (mayor atraso primero), independientemente del orden del repo."""
    e1 = _event("nuevo", _TODAY - timedelta(days=1))
    e2 = _event("viejo", _TODAY - timedelta(days=5))
    e3 = _event("medio", _TODAY - timedelta(days=3))
    uc = _use_case(events=[e1, e2, e3])
    result = await uc.execute(
        is_superadmin=False, full_name=_FULL_NAME, today=_TODAY, cutoff_days=30
    )
    ids = [a.event.id for a in result]
    assert ids == ["viejo", "medio", "nuevo"]


@pytest.mark.asyncio
async def test_usuario_sin_operador_matcheado_no_ve_nada() -> None:
    repo = _mock_repo([_event("e1", _TODAY - timedelta(days=1))])
    repo.find_operador_by_nombre.return_value = None
    uc = _use_case(repo_mock=repo)
    result = await uc.execute(
        is_superadmin=False, full_name="Nadie Conocido", today=_TODAY, cutoff_days=30
    )
    assert result == []
    repo.list_events.assert_not_awaited()


@pytest.mark.asyncio
async def test_eventos_cubiertos_de_otro_operador_no_aparecen() -> None:
    """Si el usuario tiene un override cubriendo a otro operador, los eventos
    de ese operador cubrierto NO deben aparecer en el backlog — el arrastre
    es responsabilidad del operador original, no del reemplazante."""
    otro_operador_id = "canal-directo"
    propio = _event("propio", _TODAY - timedelta(days=1), operador_id=_OPERADOR_ID)
    cubierto = _event("cubierto", _TODAY - timedelta(days=5), operador_id=otro_operador_id)

    repo = AsyncMock()
    repo.list_operadores.return_value = [
        Operador(id=_OPERADOR_ID, nombre=_FULL_NAME),
        Operador(id=otro_operador_id, nombre="Contadores CanalDirecto"),
    ]
    # find_operador_by_nombre se llama con el full_name del usuario logueado
    repo.find_operador_by_nombre.return_value = Operador(id=_OPERADOR_ID, nombre=_FULL_NAME)

    override = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=otro_operador_id,
        operador_reemplazante_id=_OPERADOR_ID,
        vigente_desde=date(2026, 7, 1),
        vigente_hasta=date(2026, 8, 31),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )
    overrides_mock = _mock_overrides()
    overrides_mock.list_activos_por_reemplazante.return_value = [override]

    async def list_events(start_date: str, end_date: str, operador_id: str | None):
        if operador_id == _OPERADOR_ID:
            return [propio]
        if operador_id == otro_operador_id:
            return [cubierto]
        return []

    repo.list_events.side_effect = list_events

    uc = _use_case(repo_mock=repo, overrides_mock=overrides_mock)
    result = await uc.execute(
        is_superadmin=False, full_name=_FULL_NAME, today=_TODAY, cutoff_days=30
    )

    ids = {a.event.id for a in result}
    assert "propio" in ids
    assert "cubierto" not in ids


@pytest.mark.asyncio
async def test_evento_propio_cubierto_viaja_anotado_y_no_se_filtra() -> None:
    """Un pendiente del propio operador que alguien está cubriendo debe
    seguir apareciendo (sigue siendo responsabilidad del ausente) y viaja
    con la anotación de cobertura intacta."""
    ayer = _TODAY - timedelta(days=1)
    e = _event("propio-cubierto", ayer, operador_id=_OPERADOR_ID)
    repo = _mock_repo([e])
    repo.list_operadores.return_value = [
        Operador(id=_OPERADOR_ID, nombre=_FULL_NAME, color="#d9534f"),
        Operador(id="vipaez", nombre="Victor Paez", color="#5cb85c"),
    ]

    override = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=_OPERADOR_ID,
        operador_reemplazante_id="vipaez",
        vigente_desde=date(2026, 8, 1),
        vigente_hasta=date(2026, 8, 15),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )
    overrides_mock = _mock_overrides()
    overrides_mock.list_activos_por_ausente.return_value = [override]

    uc = _use_case(repo_mock=repo, overrides_mock=overrides_mock)
    result = await uc.execute(
        is_superadmin=False, full_name=_FULL_NAME, today=_TODAY, cutoff_days=30
    )

    assert len(result) == 1
    assert result[0].event.id == "propio-cubierto"
    assert result[0].cobertura is not None
    assert result[0].cobertura.operador_reemplazante_id == "vipaez"


@pytest.mark.asyncio
async def test_superadmin_ve_pendientes_de_todos() -> None:
    """Un superadmin no necesita match de operador y ve todos los pendientes."""
    repo = _mock_repo()
    repo.list_events.return_value = [
        _event("e1", _TODAY - timedelta(days=2), operador_id="749"),
        _event("e2", _TODAY - timedelta(days=1), operador_id="vipaez"),
    ]
    uc = _use_case(repo_mock=repo)
    result = await uc.execute(
        is_superadmin=True, full_name="Alguien Admin", today=_TODAY, cutoff_days=30
    )
    assert len(result) == 2
    repo.find_operador_by_nombre.assert_not_awaited()
