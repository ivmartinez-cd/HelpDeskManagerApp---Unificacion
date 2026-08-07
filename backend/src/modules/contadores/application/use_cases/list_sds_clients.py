from src.modules.contadores.application.dtos.sds_dtos import SdsClientResult
from src.modules.contadores.domain.repositories.meter_client_config_repository import (
    MeterClientConfigRepository,
)
from src.modules.contadores.domain.repositories.sds_client_provider import SdsClientProvider
from src.modules.contadores.domain.value_objects.meter_source import MeterSource


class ListSdsClientsUseCase:
    """Obtiene clientes de la API de SDS y los combina con la preferencia
    `suma_color` guardada en la base de datos."""

    def __init__(
        self,
        sds_provider: SdsClientProvider,
        config_repo: MeterClientConfigRepository,
    ) -> None:
        self._sds_provider = sds_provider
        self._config_repo = config_repo

    async def execute(self) -> list[SdsClientResult]:
        active_customers = await self._sds_provider.list_active_customers()
        configs = await self._config_repo.list_by_source(MeterSource("sds"))
        config_map = {c.customer_id: c.suma_color for c in configs}

        return [
            SdsClientResult(
                id=c.id,
                name=c.name,
                suma_color=config_map.get(c.id, False),
            )
            for c in active_customers
        ]
