"""Implementación httpx del puerto SdsPortalGateway (scraping del PortalWeb de SDS).

Diferencias clave respecto al legacy (requests síncrono):
- httpx async con follow_redirects=True explícito (trampa 1: sin esto resp.url nunca
  es /login, el re-login nunca ocurre y la baja falla con un error engañoso).
- Sesión manejada por AsyncClient (cookie jar persistente para JSESSIONID).
- NUNCA re-loguear especulativamente: solo ante redirect confirmado a /login. Un
  re-login de más dispara el throttle del portal y bloquea el lote entero
  (incidente real de producción, 2026-07-30).
- El POST de baja NUNCA se reintenta: la operación es irreversible.
"""

import logging

import httpx

from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.infrastructure.portal.portal_parsing import (
    MAX_HTML_BYTES,
    extract_csrf_token,
    is_delete_success,
    parse_delivery_location_contact,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 5.0
_READ_TIMEOUT = 30.0
_TIMEOUT = httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT)


class HttpxSdsPortalGateway:
    """Scraper del PortalWeb de SDS Insight (login humano por cookie JSESSIONID).

    Una instancia por proceso — el AsyncClient conserva el cookie jar entre llamadas.
    Construirla con `lru_cache` en wiring.py (un cliente singleton, no uno por request).
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=_TIMEOUT,
        )
        self._logged_in = False

    async def _login(self) -> None:
        login_url = f"{self._base_url}/PortalWeb/login"
        # GET previo: el portal espera un JSESSIONID ya creado antes del POST.
        await self._client.get(login_url)
        resp = await self._client.post(
            login_url,
            data={"username": self._username, "password": self._password},
        )
        resp.raise_for_status()
        if "/PortalWeb/login" in str(resp.url):
            raise ExternalServiceError(
                "Login al PortalWeb de SDS falló — verificar "
                "SDS_PORTAL_USERNAME/SDS_PORTAL_PASSWORD"
            )
        self._logged_in = True
        logger.info("PortalWeb SDS login OK")

    async def _ensure_login(self, force: bool = False) -> None:
        if force or not self._logged_in:
            self._logged_in = False
            await self._login()

    async def _fetch_csrf_token(self, device_id: int) -> tuple[str | None, bool]:
        """(token, session_expired). session_expired solo es True si hubo redirect
        confirmado a /login — es la única señal válida para forzar re-login."""
        resp = await self._client.get(
            f"{self._base_url}/PortalWeb/devices/edit",
            params={"d": device_id, "action": "delete"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        resp.raise_for_status()
        session_expired = "/PortalWeb/login" in str(resp.url)
        html_content = resp.text[:MAX_HTML_BYTES]
        return extract_csrf_token(html_content), session_expired

    async def ensure_login(self) -> None:
        """Pre-calienta la sesión antes de disparar lookups en paralelo."""
        await self._ensure_login()

    async def get_delivery_location_contact(
        self, customer_id: int, location_id: int
    ) -> ContactInfo | None:
        """Contacto cargado en la delivery location, o None si no tiene ninguno.

        Lanza ExternalServiceError si la location no existe o el parsing falla.
        """
        await self._ensure_login()
        url = (
            f"{self._base_url}/PortalWeb/customers/{customer_id}"
            f"/delivery-locations/{location_id}"
        )
        resp = await self._client.get(url)
        if resp.status_code == 404:
            raise ExternalServiceError(
                f"Delivery location {location_id} (cliente {customer_id}) no existe"
            )
        resp.raise_for_status()
        html_content = resp.text[:MAX_HTML_BYTES]
        try:
            return parse_delivery_location_contact(html_content, location_id)
        except ValueError as exc:
            raise ExternalServiceError(str(exc)) from exc

    async def delete_device(self, device_id: int) -> None:
        await self._ensure_login()

        csrf_token, session_expired = await self._fetch_csrf_token(device_id)
        if csrf_token is None and session_expired:
            # Un solo re-login ante sesión vencida confirmada — no más (incidente 2026-07-30).
            await self._ensure_login(force=True)
            csrf_token, session_expired = await self._fetch_csrf_token(device_id)
        if csrf_token is None:
            raise ExternalServiceError(
                f"No se pudo obtener el CSRF del formulario de baja del equipo {device_id} "
                "(¿el equipo ya no admite baja, o cambió la estructura del PortalWeb?)"
            )

        # NUNCA reintentar este POST — es una baja real e irreversible.
        resp = await self._client.post(
            f"{self._base_url}/PortalWeb/devices/edit",
            data={
                "__csrftoken": csrf_token,
                "action": "delete",
                "d": str(device_id),
                "deleteMode": "Y",
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self._base_url}/PortalWeb/devices",
            },
        )
        resp.raise_for_status()
        body = resp.text[:MAX_HTML_BYTES]
        if not is_delete_success(body):
            raise ExternalServiceError(
                f"El PortalWeb no confirmó la baja del equipo {device_id}: {body[:300]!r}"
            )
        logger.info("Equipo %d dado de baja en el PortalWeb de SDS", device_id)
