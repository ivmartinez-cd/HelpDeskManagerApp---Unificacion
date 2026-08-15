"""Puerto: portal web de HP SDS (scraping)."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class EventLogsResult:
    """Resultado parseado de fetch_event_logs: TSV listo para analizar + URLs de ayuda."""

    tsv: str
    help_urls: dict[str, dict[str, Any]] = field(default_factory=dict)


class HpPortalGateway(Protocol):
    async def search_device(self, serial: str) -> dict[str, str]:
        """Devuelve {'id': device_id, 'model_name': model_name}."""
        ...

    async def fetch_event_logs(self, device_id: str, days: int = 30) -> EventLogsResult:
        """Parsea los event logs del equipo: TSV de 6 cols + dict de help_urls por código."""
        ...

    async def fetch_remote_ews_url(self, device_id: str) -> str | None:
        """Devuelve el link one-time JWT a ews.hpjamservices.com."""
        ...

    async def get_hp_operations(self, device_id: str) -> list[dict[str, Any]]:
        """Tabla de operaciones HP Smart del dispositivo."""
        ...

    async def refresh_hp_cache(self, device_id: str) -> list[dict[str, Any]]:
        """Dispara la actualización de caché. Devuelve baseline de operaciones."""
        ...

    async def fetch_solution_content(self, url: str) -> str | None:
        """Fetchea el contenido de una página de solución HP usando la sesión SDS."""
        ...
