import json
import logging
from pathlib import Path
from typing import Any

import httpx

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.ports.calendar_port import CalendarPort
from src.modules.contadores.infrastructure.gestion.gestion_session_refresher import (
    refresh_gestion_session,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_REDIRECT_STATUS_CODES = (301, 302, 303)


class GestionPlanificacionClient(CalendarPort):
    """Cliente HTTP que consume los eventos de facturación (ajax-by-rango) de
    la web de gestión. El catálogo de operadores ya no se scrapea de acá —
    ver PyodbcOperadorGateway y ADR-012.

    La sesión (PHPSESSID) se renueva sola vía login Symfony cuando falta o
    vence (redirect a /login) — ver gestion_session_refresher.py. `cookie`
    sigue existiendo como override explícito para tests.
    """

    def __init__(
        self,
        base_url: str | None = None,
        cookie: str | None = None,
        timeout: float | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.gestion_web_base_url).rstrip("/")
        self._explicit_cookie = cookie
        self._session_file = settings.gestion_session_file
        self._timeout = timeout or settings.gestion_web_timeout_seconds

    async def get_events(
        self,
        start_date: str,
        end_date: str,
        operador_id: str | None = None,
        tipo_evento: list[str] | None = None,
        solo_facturacion: bool = True,
    ) -> list[CalendarEvent]:
        params = self._build_params(start_date, end_date, operador_id, tipo_evento)
        response = await self._get(
            "/planificacion/ajax-by-rango",
            params=params,
            extra_headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        try:
            data = list(response.json())
        except Exception as exc:
            raise ExternalServiceError(f"Respuesta inválida de gestión: {exc}") from exc
        return self._parse_events(data, operador_id, solo_facturacion)

    def _build_params(
        self,
        start_date: str,
        end_date: str,
        operador_id: str | None,
        tipo_evento: list[str] | None,
    ) -> dict[str, str | list[str]]:
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
        return params

    async def _ensure_cookie(self, force_refresh: bool = False) -> str:
        if not force_refresh:
            cached = self._read_cached_cookie()
            if cached:
                return cached
        session_data = await refresh_gestion_session(self._session_file)
        return str(session_data["cookie"])

    def _read_cached_cookie(self) -> str | None:
        path = Path(self._session_file)
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                cookie = json.load(f).get("cookie")
                return str(cookie) if cookie else None
        except Exception as exc:
            logger.warning(
                "Sesión de Gestión cacheada ilegible, se va a renovar",
                extra={"session_file": str(path)},
                exc_info=exc,
            )
            return None

    async def _get(
        self,
        path: str,
        *,
        params: dict[str, str | list[str]] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        cookie = self._explicit_cookie or await self._ensure_cookie()
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=False) as client:
            response = await self._request(client, path, params, cookie, extra_headers)
            if response.status_code in _REDIRECT_STATUS_CODES and not self._explicit_cookie:
                cookie = await self._ensure_cookie(force_refresh=True)
                response = await self._request(client, path, params, cookie, extra_headers)
            try:
                response.raise_for_status()
                return response
            except Exception as exc:
                raise ExternalServiceError(
                    f"Error al consultar el servicio de gestión: {exc}"
                ) from exc

    async def _request(
        self,
        client: httpx.AsyncClient,
        path: str,
        params: dict[str, str | list[str]] | None,
        cookie: str,
        extra_headers: dict[str, str] | None,
    ) -> httpx.Response:
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            **(extra_headers or {}),
        }
        try:
            return await client.get(f"{self._base_url}{path}", params=params, headers=headers)
        except Exception as exc:
            raise ExternalServiceError(
                f"Error al consultar el servicio de gestión: {exc}"
            ) from exc

    def _parse_events(
        self,
        data: list[dict[str, Any]],
        operador_id: str | None,
        solo_facturacion: bool,
    ) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for item in data:
            string_tipo = item.get("stringTipoEvento") or ""
            title_text = item.get("title") or ""
            if solo_facturacion and not (
                "Facturaci" in string_tipo or "(Facturaci" in title_text
            ):
                continue
            events.append(self._to_event(item, operador_id))
        return events

    def _to_event(self, item: dict[str, Any], operador_id: str | None) -> CalendarEvent:
        raw_id = item.get("id")
        if isinstance(raw_id, list):
            event_id = str(raw_id[0]) if raw_id else ""
        else:
            event_id = str(raw_id) if raw_id is not None else ""

        return CalendarEvent(
            id=event_id,
            title=item.get("title", ""),
            start=item.get("start", ""),
            # Los eventos de facturación traen su operador (username) en la
            # propia respuesta; el parámetro del filtro queda como fallback.
            operador_id=item.get("operador") or operador_id,
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
