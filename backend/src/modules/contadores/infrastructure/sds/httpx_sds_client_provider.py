from __future__ import annotations

import base64
import logging
from typing import Any, cast

import httpx

from src.modules.contadores.domain.entities.sds_client import SdsClient
from src.modules.contadores.infrastructure.csv.auto_csv_writer import (
    AutoCsvTarget,
    write_auto_csv,
)
from src.modules.contadores.infrastructure.sds.sds_export import (
    MeterRowContext,
    build_meter_rows,
    calculate_min_date,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class HttpxSdsClientProvider:
    """Implementación de SdsClientProvider usando httpx para conectarse a la API de HP SDS LATAM."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def list_active_customers(self) -> list[SdsClient]:
        token = await self._get_auth_token()
        url = f"{self._settings.sds_base_url}/api/customers"
        headers = {"Authorization": token, "Accept": "application/json"}
        timeout = httpx.Timeout(self._settings.sds_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
        except Exception as exc:
            raise ExternalServiceError(f"Error al conectar con la API de SDS: {exc}") from exc

        if response.status_code != 200:
            raise ExternalServiceError(
                f"Error al obtener clientes SDS: {response.status_code} - {response.text}"
            )
        return _to_active_clients(response.json())

    async def export_meters_to_csv(
        self,
        *,
        customer_id: str,
        customer_name: str,
        max_date: str,
        output_dir: str,
        suma_color: bool = False,
    ) -> str:
        token = await self._get_auth_token()
        meters = await self._get_device_meters(token, customer_id, max_date)
        if not meters:
            raise ExternalServiceError(
                f"No se encontraron contadores para el cliente '{customer_name}' "
                "en la fecha especificada."
            )
        min_dt = calculate_min_date(max_date)
        serial_map = await self._get_device_serial_map(token, customer_id)
        ctx = MeterRowContext(
            customer_id=customer_id, serial_map=serial_map, min_dt=min_dt, suma_color=suma_color
        )
        rows = build_meter_rows(meters, ctx)
        target = AutoCsvTarget(
            prefix="SDS", name=customer_name, max_date=max_date,
            output_dir=output_dir, suma_color=suma_color,
        )
        return str(write_auto_csv(rows, target))

    async def _get_auth_token(self) -> str:
        url = f"{self._settings.sds_base_url}/login"
        headers = self._login_headers()
        timeout = httpx.Timeout(self._settings.sds_timeout_seconds)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers)
        except Exception as exc:
            raise ExternalServiceError(f"Error al autenticar en SDS: {exc}") from exc

        if response.status_code == 200:
            return _extract_login_token(response)
        raise ExternalServiceError(
            f"Error al autenticar en SDS: {response.status_code} - {response.text}"
        )

    def _login_headers(self) -> dict[str, str]:
        """Basic auth con api_key:api_secret, como exige el `/login` de SDS."""
        credentials = (
            f"{self._settings.sds_api_key}:{self._settings.sds_api_secret.get_secret_value()}"
        )
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

    async def _get_device_meters(
        self, token: str, customer_id: str, max_date: str
    ) -> list[dict[str, Any]]:
        url = f"{self._settings.sds_base_url}/api/devices/meters/latestbydate/{customer_id}"
        params = {
            "maxReadDateTimeLocal": _to_max_read_datetime_local(max_date),
            "includeExtendedMeters": "true",
        }
        headers = {"Authorization": token, "Accept": "application/json"}
        timeout = httpx.Timeout(self._settings.sds_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers, params=params)
        except Exception as exc:
            raise ExternalServiceError(f"Error al obtener contadores SDS: {exc}") from exc

        if response.status_code == 200:
            return cast(list[dict[str, Any]], response.json())
        raise ExternalServiceError(
            f"Error al obtener contadores SDS: {response.status_code} - {response.text}"
        )

    async def _get_device_serial_map(self, token: str, customer_id: str) -> dict[Any, str]:
        url = f"{self._settings.sds_base_url}/api/devices"
        headers = {"Authorization": token, "Accept": "application/json"}
        params = {"customerId": customer_id}
        timeout = httpx.Timeout(self._settings.sds_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers, params=params)
        except Exception as exc:
            logger.warning(
                "No se pudo obtener el mapa de números de serie SDS",
                extra={"customer_id": customer_id},
                exc_info=exc,
            )
            return {}

        if response.status_code == 200:
            return _to_serial_map(response.json())
        return {}


def _to_active_clients(all_customers: list[dict[str, Any]]) -> list[SdsClient]:
    active = [
        SdsClient(
            id=str(c["id"]) if "id" in c else str(c.get("customerId", "")),
            name=str(c.get("name", "")),
            status=str(c.get("status", "ACTIVE")).upper(),
        )
        for c in all_customers
        if str(c.get("status", "")).upper() == "ACTIVE"
    ]
    return sorted(active, key=lambda c: c.name)


def _to_serial_map(devices: list[dict[str, Any]]) -> dict[Any, str]:
    return {d["deviceId"]: str(d.get("serialNumber", "")) for d in devices if "deviceId" in d}


def _extract_login_token(response: httpx.Response) -> str:
    """El token viene en el body JSON (`access_token`/`token`) o, si no, en el
    header `Authorization` de la respuesta de login."""
    is_json = response.headers.get("content-type", "").startswith("application/json")
    data = response.json() if is_json else {}
    token = data.get("access_token") or data.get("token")
    if token:
        return f"Bearer {token}"
    auth_header = response.headers.get("Authorization")
    if auth_header:
        return cast(str, auth_header)
    raise ExternalServiceError("No se pudo extraer el token del response de login SDS.")


def _to_max_read_datetime_local(max_date: str) -> str:
    """La API de HP Insight exige `maxReadDateTimeLocal` en formato exacto
    `yyyy-MM-ddTHH:mm:ss` (400 Bad Request con cualquier otra cosa, incluida una fecha
    sin hora). El frontend manda solo la fecha (`<input type="date">`), así que se le
    agrega el final del día para incluir todas las lecturas de esa fecha."""
    date_part = max_date.split("T")[0]
    return f"{date_part}T23:59:59"
