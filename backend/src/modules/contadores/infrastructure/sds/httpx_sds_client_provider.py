from __future__ import annotations

import base64
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import httpx

from src.modules.contadores.domain.entities.sds_client import SdsClient
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

        all_customers: list[dict[str, Any]] = response.json()
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
            msg = (
                f"No se encontraron contadores para el cliente '{customer_name}' "
                "en la fecha especificada."
            )
            raise ExternalServiceError(msg)

        min_dt = _calculate_min_date(max_date)
        serial_map = await self._get_device_serial_map(token, customer_id)

        rows = []
        for device in meters:
            device_id = device.get("deviceId")
            serie = serial_map.get(
                device_id, str(device_id) if device_id is not None else ""
            )

            raw_date = str(
                device.get("readingDate") or (str(device.get("readingDateTime", ""))[:10])
            )
            try:
                device_dt = datetime.strptime(raw_date, "%Y-%m-%d")
                if min_dt and device_dt < min_dt:
                    continue
                fecha = device_dt.strftime("%d/%m/%Y")
            except Exception as exc:
                logger.debug(
                    "No se pudo parsear la fecha de un contador SDS, uso el valor crudo",
                    extra={"customer_id": customer_id, "raw_date": raw_date},
                    exc_info=exc,
                )
                fecha = raw_date

            engine_cycles = int(device.get("engineCycles") or 0)
            mono_pages = int(device.get("monoPages") or 0)
            colour_pages = int(device.get("colourPages") or 0)
            is_color = colour_pages > 0

            if suma_color and is_color:
                rows.append(
                    {
                        "SERIE": serie,
                        "FECHA": fecha,
                        "TIPO": 21,
                        "CLASE_10": 20,
                        "CONTADOR_10": engine_cycles,
                        "CLASE_20": "",
                        "CONTADOR_20": 0,
                        "MOTIVO": "",
                        "OBSERVACION": "",
                    }
                )
            else:
                rows.append(
                    {
                        "SERIE": serie,
                        "FECHA": fecha,
                        "TIPO": 21,
                        "CLASE_10": 10,
                        "CONTADOR_10": mono_pages,
                        "CLASE_20": 20 if is_color else "",
                        "CONTADOR_20": colour_pages if is_color else 0,
                        "MOTIVO": "",
                        "OBSERVACION": "",
                    }
                )

        date_str = max_date.split("T")[0].replace("-", "")
        safe_name = (
            "".join([c for c in customer_name if c.isalnum() or c in (" ", "_")])
            .strip()
            .replace(" ", "_")
        )
        suffix = "_SumaColor" if suma_color else ""
        filename = f"SDS_{safe_name}_{date_str}{suffix}_AutoCSV.csv"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "SERIE",
            "FECHA",
            "TIPO",
            "CLASE_10",
            "CONTADOR_10",
            "CLASE_20",
            "CONTADOR_20",
            "MOTIVO",
            "OBSERVACION",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

        return str(output_path)

    async def _get_auth_token(self) -> str:
        url = f"{self._settings.sds_base_url}/login"
        credentials = (
            f"{self._settings.sds_api_key}:{self._settings.sds_api_secret.get_secret_value()}"
        )
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(self._settings.sds_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers)
        except Exception as exc:
            raise ExternalServiceError(f"Error al autenticar en SDS: {exc}") from exc

        if response.status_code == 200:
            is_json = response.headers.get("content-type", "").startswith("application/json")
            data = response.json() if is_json else {}
            token = data.get("access_token") or data.get("token")
            if token:
                return f"Bearer {token}"
            auth_header = response.headers.get("Authorization")
            if auth_header:
                return cast(str, auth_header)
            raise ExternalServiceError("No se pudo extraer el token del response de login SDS.")
        raise ExternalServiceError(
            f"Error al autenticar en SDS: {response.status_code} - {response.text}"
        )

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
            devices = response.json()
            return {
                d["deviceId"]: str(d.get("serialNumber", ""))
                for d in devices
                if "deviceId" in d
            }
        return {}


def _to_max_read_datetime_local(max_date: str) -> str:
    """La API de HP Insight exige `maxReadDateTimeLocal` en formato exacto
    `yyyy-MM-ddTHH:mm:ss` (400 Bad Request con cualquier otra cosa, incluida una fecha
    sin hora). El frontend manda solo la fecha (`<input type="date">`), así que se le
    agrega el final del día para incluir todas las lecturas de esa fecha."""
    date_part = max_date.split("T")[0]
    return f"{date_part}T23:59:59"


def _calculate_min_date(max_date: str) -> datetime | None:
    try:
        date_part = max_date.split("T")[0]
        if "-" in date_part:
            y, m, d = date_part.split("-")
            max_dt = datetime(int(y), int(m), int(d))
        else:
            max_dt = datetime.fromisoformat(date_part)
        return max_dt - timedelta(days=30)
    except Exception as exc:
        logger.warning(
            "No se pudo calcular la fecha mínima SDS, no se va a filtrar por fecha",
            extra={"max_date": max_date},
            exc_info=exc,
        )
        return None
