"""Fakes en memoria de los gateways externos de analisis-log-hp (portal SDS,
Insight, Anthropic, wsAyC) para tests de application puros."""

from __future__ import annotations

from typing import Any

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsReplacement
from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import EventLogsResult


class FakeHpPortalGateway:
    def __init__(
        self,
        *,
        device: dict[str, str] | None = None,
        logs: EventLogsResult | None = None,
        solution_content: str | None = "<p>vivo</p>",
        solution_error: Exception | None = None,
        search_error: Exception | None = None,
    ) -> None:
        self.device = device or {"id": "777", "model_name": "HP M404"}
        self.logs = logs or EventLogsResult(tsv="")
        self.solution_content = solution_content
        self.solution_error = solution_error
        self.search_error = search_error
        self.calls: list[tuple[str, Any]] = []

    async def search_device(self, serial: str) -> dict[str, str]:
        self.calls.append(("search_device", serial))
        if self.search_error:
            raise self.search_error
        return self.device

    async def fetch_event_logs(self, device_id: str, days: int = 30) -> EventLogsResult:
        self.calls.append(("fetch_event_logs", (device_id, days)))
        return self.logs

    async def fetch_remote_ews_url(self, device_id: str) -> str | None:
        self.calls.append(("fetch_remote_ews_url", device_id))
        return f"https://ews/{device_id}"

    async def get_hp_operations(self, device_id: str) -> list[dict[str, Any]]:
        self.calls.append(("get_hp_operations", device_id))
        return [{"operation": "Op", "sent": "hoy"}]

    async def refresh_hp_cache(self, device_id: str) -> list[dict[str, Any]]:
        self.calls.append(("refresh_hp_cache", device_id))
        return [{"operation": "RefreshHPCloudDeviceActionCache", "sent": "ayer"}]

    async def fetch_solution_content(self, url: str) -> str | None:
        self.calls.append(("fetch_solution_content", url))
        if self.solution_error:
            raise self.solution_error
        return self.solution_content


class FakeHpInsightGateway:
    def __init__(
        self,
        *,
        device: dict[str, Any] | None = None,
        search_error: Exception | None = None,
    ) -> None:
        self.device = device
        self.search_error = search_error
        self.calls: list[tuple[str, Any]] = []

    async def search_by_serial(self, serial: str) -> dict[str, Any] | None:
        self.calls.append(("search_by_serial", serial))
        if self.search_error:
            raise self.search_error
        return self.device

    async def get_device_consumables(self, device_id: int) -> list[dict[str, Any]]:
        self.calls.append(("consumables", device_id))
        return [{"color": "black", "level": 40}]

    async def get_device_alerts_current(self, device_id: int) -> list[dict[str, Any]]:
        self.calls.append(("alerts_current", device_id))
        return [{"alert": "current"}]

    async def get_device_alerts_history(
        self,
        device_id: int,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(("alerts_history", (device_id, from_date, to_date, max_results)))
        return [{"alert": "history"}]

    async def get_device_meters_history(
        self, device_id: int, days: int = 90
    ) -> list[dict[str, Any]]:
        self.calls.append(("meters", (device_id, days)))
        return [{"meter": days}]

    async def get_devices(self, customer_id: int) -> list[dict[str, Any]]:
        self.calls.append(("devices", customer_id))
        return [
            {"deviceId": 1, "serialNumber": "S1", "extendedFields": {"zone": "Z", "model": "M"}},
            {"deviceId": 2, "serialNumber": None},
        ]

    async def get_customers(self) -> list[dict[str, Any]]:
        self.calls.append(("customers", None))
        return [{"customerId": 1, "name": "Yaguar"}, {"customerId": 2, "customerName": "Otro"}]


class FakeAiGateway:
    def __init__(self, text: str = '{"despacho": "si"}', tokens: dict[str, int] | None = None):
        self.text = text
        self.tokens = tokens or {"input": 1000, "output": 200, "cache_write": 0, "cache_read": 0}
        self.calls: list[tuple[str, dict[str, Any], str]] = []

    async def diagnose(self, payload: dict[str, Any], model: str) -> tuple[str, dict[str, int]]:
        self.calls.append(("diagnose", payload, model))
        return self.text, self.tokens

    async def generate_pdf_summary(
        self, payload: dict[str, Any], model: str
    ) -> tuple[str, dict[str, int]]:
        self.calls.append(("pdf", payload, model))
        return self.text, self.tokens


class FakeCdsGateway:
    def __init__(
        self,
        *,
        machine: tuple[str, str] | None = ("M1", "E1"),
        incidents: list[dict[str, str]] | None = None,
        counters: list[dict[str, str]] | None = None,
        details_error: Exception | None = None,
    ) -> None:
        self.machine = machine
        self.incidents = incidents or []
        self.counters = counters or []
        self.details_error = details_error
        self.detail_calls: list[str] = []

    async def get_machine_by_serial(self, serial: str) -> tuple[str, str] | None:
        self.serial = serial
        return self.machine

    async def get_machine_incidents(self, machine_id: str, empresa_id: str) -> list[dict[str, str]]:
        return self.incidents

    async def get_counters(self, machine_id: str) -> list[dict[str, str]]:
        return self.counters

    async def get_incident_replacements(self, incident_id: str) -> list[CdsReplacement]:
        self.detail_calls.append(incident_id)
        if self.details_error:
            raise self.details_error
        return [CdsReplacement(articulo=f"rep-{incident_id}", cantidad=1)]

    async def get_incident_jobs(self, incident_id: str) -> list[str]:
        return [f"tarea-{incident_id}"]
