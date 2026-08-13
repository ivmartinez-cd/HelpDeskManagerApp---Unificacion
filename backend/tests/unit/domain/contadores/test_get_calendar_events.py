import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)


def _event(event_id: str, cliente: str | None = None, start: str = "2026-08-11") -> CalendarEvent:
    return CalendarEvent(
        id=event_id, title="[Facturación]: X", start=f"{start}T00:00:00-03:00", cliente=cliente
    )


def _mock_overrides(
    activos_por_ausente: list[AsignacionOverride] | None = None,
    activos_por_reemplazante: list[AsignacionOverride] | None = None,
) -> AsyncMock:
    mock = AsyncMock()
    mock.list_activos_por_ausente.return_value = activos_por_ausente or []
    mock.list_activos_por_reemplazante.return_value = activos_por_reemplazante or []
    return mock


def _override(**overrides: object) -> AsignacionOverride:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": "749",
        "operador_reemplazante_id": "vipaez",
        "vigente_desde": date(2026, 8, 1),
        "vigente_hasta": date(2026, 8, 15),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": None,
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_superadmin_sees_all_operadores() -> None:
    mock_repo = AsyncMock()
    mock_repo.list_events.return_value = [_event("123")]

    use_case = GetCalendarEventsUseCase(mock_repo, _mock_overrides())
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        is_superadmin=True,
        full_name="Ivan Martinez",
    )

    result = await use_case.execute(request)

    assert len(result) == 1
    mock_repo.find_operador_by_nombre.assert_not_awaited()
    mock_repo.list_events.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", operador_id=None
    )


@pytest.mark.asyncio
async def test_superadmin_filters_by_requested_operador() -> None:
    mock_repo = AsyncMock()
    mock_repo.list_events.return_value = []

    use_case = GetCalendarEventsUseCase(mock_repo, _mock_overrides())
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        is_superadmin=True,
        full_name="Ivan Martinez",
        operador_id="vipaez",
    )

    await use_case.execute(request)

    mock_repo.find_operador_by_nombre.assert_not_awaited()
    mock_repo.list_events.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", operador_id="vipaez"
    )


@pytest.mark.asyncio
async def test_regular_user_filters_by_matched_operador() -> None:
    mock_repo = AsyncMock()
    mock_repo.find_operador_by_nombre.return_value = Operador(id="749", nombre="Ivan Martinez")
    mock_repo.list_events.return_value = []

    use_case = GetCalendarEventsUseCase(mock_repo, _mock_overrides())
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        is_superadmin=False,
        full_name="Ivan Martinez",
    )

    await use_case.execute(request)

    mock_repo.find_operador_by_nombre.assert_awaited_once_with("Ivan Martinez")
    mock_repo.list_events.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", operador_id="749"
    )


@pytest.mark.asyncio
async def test_regular_user_cannot_use_operador_filter_to_see_others() -> None:
    """Un operador_id en el request de un usuario no-superadmin se ignora —
    solo puede ver el suyo propio, nunca el de otra persona."""
    mock_repo = AsyncMock()
    mock_repo.find_operador_by_nombre.return_value = Operador(id="749", nombre="Ivan Martinez")
    mock_repo.list_events.return_value = []

    use_case = GetCalendarEventsUseCase(mock_repo, _mock_overrides())
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        is_superadmin=False,
        full_name="Ivan Martinez",
        operador_id="vipaez",
    )

    await use_case.execute(request)

    mock_repo.list_events.assert_awaited_once_with(
        start_date="2026-08-01", end_date="2026-08-31", operador_id="749"
    )


@pytest.mark.asyncio
async def test_regular_user_without_operador_match_sees_nothing() -> None:
    mock_repo = AsyncMock()
    mock_repo.find_operador_by_nombre.return_value = None

    use_case = GetCalendarEventsUseCase(mock_repo, _mock_overrides())
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        is_superadmin=False,
        full_name="Nadie Conocido",
    )

    result = await use_case.execute(request)

    assert result == []
    mock_repo.list_events.assert_not_awaited()


@pytest.mark.asyncio
async def test_evento_propio_cubierto_por_otro_no_aparece() -> None:
    """Si un override me reasigna un evento a otro operador, ese evento deja
    de estar en 'mis eventos' — lo cubre quien tenga el override."""
    mock_repo = AsyncMock()
    mock_repo.find_operador_by_nombre.return_value = Operador(id="749", nombre="Ivan Martinez")
    mock_repo.list_events.return_value = [_event("123")]
    overrides = _mock_overrides(activos_por_ausente=[_override()])

    use_case = GetCalendarEventsUseCase(mock_repo, overrides)
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        is_superadmin=False,
        full_name="Ivan Martinez",
    )

    result = await use_case.execute(request)

    assert result == []


@pytest.mark.asyncio
async def test_evento_cubierto_de_otro_operador_aparece() -> None:
    """Si tengo un override activo cubriendo a otro operador, sus eventos
    aparecen en 'mis eventos' además de los propios."""
    propio = _event("propio")
    cubierto = _event("cubierto-1")
    mock_repo = AsyncMock()
    mock_repo.find_operador_by_nombre.return_value = Operador(id="vipaez", nombre="Victor Paez")

    async def list_events(start_date: str, end_date: str, operador_id: str | None):
        return [propio] if operador_id == "vipaez" else [cubierto]

    mock_repo.list_events.side_effect = list_events
    overrides = _mock_overrides(activos_por_reemplazante=[_override()])

    use_case = GetCalendarEventsUseCase(mock_repo, overrides)
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        is_superadmin=False,
        full_name="Victor Paez",
    )

    result = await use_case.execute(request)

    assert {e.id for e in result} == {"propio", "cubierto-1"}


@pytest.mark.asyncio
async def test_gestion_planificacion_client_parse() -> None:
    sample_json = [
        {
            "id": 32629,
            "title": "[Facturación]: SUR",
            "start": "2026-07-30T00:00:00-03:00",
            "allDay": True,
            "backgroundColor": "#5cb85c",
            "borderColor": "#5cb85c",
            "type": "EF",
            "tittle_tooltip": "Facturación N 32629",
            "content_tooltip": "<strong>Cliente: </strong>NEUMATICOS ROSMI SRL",
            "stringTipoEvento": "Facturación",
            "cliente": "NEUMATICOS ROSMI SRL",
            "vendedor": "Gustavo Lagues",
            "fecha_entrega": "30/07/2026",
            "fecha_entrega_deseada": "22/07/2026",
            "sucursal_entrega": "La Plata",
            "sucursal_instalacion": "La Plata",
            "sucursal_despacho": "Bodega",
            "contacto_entrega": "Eduardo",
            "contacto_instalacion": "Eduardo",
            "bultos": 1,
            "costo_seguro": ".00",
            "costo_recambio": None,
        }
    ]

    client = GestionPlanificacionClient(base_url="http://test-gestion.com", cookie="test-cookie")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = sample_json
        mock_get.return_value = mock_response

        events = await client.get_events(
            start_date="2026-08-01", end_date="2026-08-31", operador_id="318", solo_facturacion=True
        )

        assert len(events) == 1
        assert events[0].id == "32629"
        assert events[0].cliente == "NEUMATICOS ROSMI SRL"
        assert events[0].string_tipo_evento == "Facturación"
        assert events[0].operador_id == "318"
