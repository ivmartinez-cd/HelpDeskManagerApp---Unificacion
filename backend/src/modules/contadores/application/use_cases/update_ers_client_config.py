from src.modules.contadores.application.dtos.ers_dtos import ErsClientResult
from src.modules.contadores.domain.repositories.meter_client_config_repository import (
    MeterClientConfigRepository,
)
from src.modules.contadores.domain.value_objects.meter_source import MeterSource


class UpdateErsClientConfigUseCase:
    """Guarda o actualiza la preferencia `suma_color` para un grupo de clientes de ERS."""

    def __init__(self, config_repo: MeterClientConfigRepository) -> None:
        self._config_repo = config_repo

    async def execute(
        self,
        *,
        customer_id: str,
        customer_name: str,
        suma_color: bool,
    ) -> ErsClientResult:
        updated = await self._config_repo.upsert(
            source=MeterSource("ers"),
            customer_id=customer_id,
            customer_name=customer_name,
            suma_color=suma_color,
        )
        return ErsClientResult(
            id=updated.customer_id,
            name=updated.customer_name,
            suma_color=updated.suma_color,
        )
