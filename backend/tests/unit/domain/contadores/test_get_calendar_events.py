from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)


@pytest.mark.asyncio
async def test_superadmin_sees_all_operadores() -> None:
    mock_repo = AsyncMock()
    mock_repo.list_events.return_value = [
        CalendarEvent(
            id="123", title="[Facturación]: Test Client", start="2026-08-11T00:00:00-03:00"
        )
    ]

    use_case = GetCalendarEventsUseCase(mock_repo)
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
async def test_regular_user_filters_by_matched_operador() -> None:
    mock_repo = AsyncMock()
    mock_repo.find_operador_by_nombre.return_value = Operador(id="749", nombre="Ivan Martinez")
    mock_repo.list_events.return_value = []

    use_case = GetCalendarEventsUseCase(mock_repo)
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
async def test_regular_user_without_operador_match_sees_nothing() -> None:
    mock_repo = AsyncMock()
    mock_repo.find_operador_by_nombre.return_value = None

    use_case = GetCalendarEventsUseCase(mock_repo)
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


@pytest.mark.asyncio
async def test_gestion_planificacion_client_parses_operadores_select() -> None:
    html = """
    <select id="planificacion_filter_operador_facturacion"
            name="planificacion_filter[operador_facturacion]">
        <option value="">(Seleccione un Operador de Facturación)</option>
        <option value="318">Maria Jose Vela</option>
        <option value="749">Ivan Martinez</option>
    </select>
    """
    client = GestionPlanificacionClient(base_url="http://test-gestion.com", cookie="test-cookie")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = html
        mock_get.return_value = mock_response

        operadores = await client.get_operadores()

        assert len(operadores) == 2
        assert operadores[0].id == "318"
        assert operadores[0].nombre == "Maria Jose Vela"
        assert operadores[1].id == "749"
        assert operadores[1].nombre == "Ivan Martinez"
