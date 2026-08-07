from pathlib import Path

from src.modules.contadores.application.dtos.ers_dtos import (
    ExportErsMetersRequest,
    ExportErsMetersResult,
)
from src.modules.contadores.domain.repositories.ers_client_provider import ErsClientProvider
from src.modules.contadores.domain.repositories.meter_client_config_repository import (
    MeterClientConfigRepository,
)
from src.modules.contadores.domain.value_objects.meter_source import MeterSource


class ExportErsMetersUseCase:
    """Descarga la telemetría ERS de un grupo y genera el CSV correspondiente a partir
    de la preferencia `suma_color` guardada."""

    def __init__(
        self,
        ers_provider: ErsClientProvider,
        config_repo: MeterClientConfigRepository,
    ) -> None:
        self._ers_provider = ers_provider
        self._config_repo = config_repo

    async def execute(self, request: ExportErsMetersRequest) -> ExportErsMetersResult:
        config = await self._config_repo.get(MeterSource("ers"), request.group_id)
        suma_color = config.suma_color if config else False

        csv_path = await self._ers_provider.export_meters_to_csv(
            group_id=request.group_id,
            group_name=request.group_name,
            max_date=request.max_date,
            output_dir=request.output_dir,
            suma_color=suma_color,
        )

        return ExportErsMetersResult(
            csv_path=csv_path,
            filename=Path(csv_path).name,
            group_name=request.group_name,
        )
