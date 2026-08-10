import logging

import httpx

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.ports.calendar_port import CalendarPort
from src.shared.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class GestionPlanificacionClient(CalendarPort):
    """Cliente HTTP que consume la planificación desde la web de gestión (ajax-by-rango)."""

    def __init__(
        self,
        base_url: str | None = None,
        cookie: str | None = None,
        timeout: float | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.gestion_web_base_url).rstrip("/")
        self._cookie = cookie or settings.gestion_web_cookie
        self._timeout = timeout or settings.gestion_web_timeout_seconds

    async def get_events(
        self,
        start_date: str,
        end_date: str,
        operador_id: str | None = None,
        tipo_evento: list[str] | None = None,
        solo_facturacion: bool = True,
    ) -> list[CalendarEvent]:
        url = f"{self._base_url}/planificacion/ajax-by-rango"
        params: dict[str, str | list[str]] = {
            "cliente_id": "",
            "tipo_zona": "0",
            "deposito": "",
            "operador_facturacion": operador_id or "",
            "operador_id": "",
            "filtrar": "",
            "start": start_date,
            "end": end_date,
        }

        if tipo_evento:
            params["tipo_evento[]"] = tipo_evento
        else:
            params["tipo_evento[0]"] = "EF"

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Cookie": self._cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.error("Error al consultar planificación en gestión: %s", e)
                raise RuntimeError(f"Error al consultar el servicio de gestión: {e}") from e

        events: list[CalendarEvent] = []
        for item in data:
            raw_id = item.get("id")
            if isinstance(raw_id, list):
                event_id = str(raw_id[0]) if raw_id else ""
            else:
                event_id = str(raw_id) if raw_id is not None else ""

            string_tipo = item.get("stringTipoEvento") or ""
            title_text = item.get("title") or ""

            # Si solo_facturacion está activo, filtramos por tipo de evento de facturación
            if solo_facturacion and not (
                "Facturaci" in string_tipo or "(Facturaci" in title_text
            ):
                continue

            events.append(
                CalendarEvent(
                    id=event_id,
                    title=item.get("title", ""),
                    start=item.get("start", ""),
                    all_day=item.get("allDay", True),
                    background_color=item.get("backgroundColor"),
                    border_color=item.get("borderColor"),
                    type=item.get("type"),
                    tittle_tooltip=item.get("tittle_tooltip"),
                    content_tooltip=item.get("content_tooltip"),
                    string_tipo_evento=item.get("stringTipoEvento"),
                    cliente=item.get("cliente"),
                    vendedor=item.get("vendedor"),
                    fecha_entrega=item.get("fecha_entrega"),
                    fecha_entrega_deseada=item.get("fecha_entrega_deseada"),
                    sucursal_entrega=item.get("sucursal_entrega"),
                    sucursal_instalacion=item.get("sucursal_instalacion"),
                    sucursal_despacho=item.get("sucursal_despacho"),
                    contacto_entrega=item.get("contacto_entrega"),
                    contacto_instalacion=item.get("contacto_instalacion"),
                    bultos=item.get("bultos"),
                    costo_seguro=item.get("costo_seguro"),
                    costo_recambio=item.get("costo_recambio"),
                )
            )

        return events

