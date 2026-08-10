from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)


@pytest.mark.asyncio
async def test_get_calendar_events_use_case() -> None:
    mock_port = AsyncMock()
    mock_port.get_events.return_value = [
        CalendarEvent(
            id="123",
            title="[Impresión]: Test Client",
            start="2026-08-11T00:00:00-03:00",
            cliente="Test Client",
            string_tipo_evento="Instalación",
        )
    ]

    use_case = GetCalendarEventsUseCase(mock_port)
    request = GetCalendarEventsRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        operador_id="318",
    )

    result = await use_case.execute(request)

    assert len(result) == 1
    assert result[0].id == "123"

    assert result[0].cliente == "Test Client"
    mock_port.get_events.assert_awaited_once_with(
        start_date="2026-08-01",
        end_date="2026-08-31",
        operador_id="318",
        tipo_evento=None,
        solo_facturacion=True,
    )


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

    client = GestionPlanificacionClient(
        base_url="http://test-gestion.com", cookie="test-cookie"
    )

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = sample_json
        mock_get.return_value = mock_response

        events = await client.get_events(
            start_date="2026-08-01", end_date="2026-08-31", solo_facturacion=True
        )

        assert len(events) == 1
        assert events[0].id == "32629"
        assert events[0].cliente == "NEUMATICOS ROSMI SRL"
        assert events[0].string_tipo_evento == "Facturación"
