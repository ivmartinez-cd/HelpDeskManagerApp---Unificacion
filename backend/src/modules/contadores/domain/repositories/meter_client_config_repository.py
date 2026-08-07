from typing import Protocol

from src.modules.contadores.domain.entities.meter_client_config import MeterClientConfig
from src.modules.contadores.domain.value_objects.meter_source import MeterSource


class MeterClientConfigRepository(Protocol):
    """`list_by_source` alimenta el merge de "suma_color guardado" contra el
    listado de clientes que trae la API externa (SDS/ERS) en vivo — ver
    `sds_clients_list`/`ers_clients_list` de la app vieja."""

    async def list_by_source(self, source: MeterSource) -> list[MeterClientConfig]: ...
    async def get(self, source: MeterSource, customer_id: str) -> MeterClientConfig | None: ...
    async def upsert(
        self, *, source: MeterSource, customer_id: str, customer_name: str, suma_color: bool
    ) -> MeterClientConfig: ...
