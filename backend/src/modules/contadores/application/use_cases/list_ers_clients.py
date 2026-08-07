from src.modules.contadores.application.dtos.ers_dtos import ErsClientResult
from src.modules.contadores.domain.repositories.ers_client_provider import ErsClientProvider
from src.modules.contadores.domain.repositories.meter_client_config_repository import (
    MeterClientConfigRepository,
)
from src.modules.contadores.domain.value_objects.meter_source import MeterSource


class ListErsClientsUseCase:
    """Obtiene los grupos de dispositivos desde ERS y los combina con la preferencia
    `suma_color` guardada en la base de datos para `MeterSource("ers")`."""

    def __init__(
        self,
        ers_provider: ErsClientProvider,
        config_repo: MeterClientConfigRepository,
    ) -> None:
        self._ers_provider = ers_provider
        self._config_repo = config_repo

    async def execute(self) -> list[ErsClientResult]:
        active_customers = await self._ers_provider.list_active_customers()
        configs = await self._config_repo.list_by_source(MeterSource("ers"))
        config_map = {c.customer_id: c.suma_color for c in configs}

        return [
            ErsClientResult(
                id=c.id,
                name=c.name,
                suma_color=config_map.get(c.id, False),
            )
            for c in active_customers
        ]
