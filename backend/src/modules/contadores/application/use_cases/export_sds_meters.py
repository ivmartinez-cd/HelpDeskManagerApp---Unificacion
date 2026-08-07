from pathlib import Path

from src.modules.contadores.application.dtos.sds_dtos import (
    ExportSdsMetersRequest,
    ExportSdsMetersResult,
)
from src.modules.contadores.domain.repositories.meter_client_config_repository import (
    MeterClientConfigRepository,
)
from src.modules.contadores.domain.repositories.sds_client_provider import SdsClientProvider
from src.modules.contadores.domain.value_objects.meter_source import MeterSource


class ExportSdsMetersUseCase:
    """Descarga contadores SDS y genera el CSV correspondiente a partir de la
    preferencia suma_color guardada."""

    def __init__(
        self,
        sds_provider: SdsClientProvider,
        config_repo: MeterClientConfigRepository,
    ) -> None:
        self._sds_provider = sds_provider
        self._config_repo = config_repo

    async def execute(self, request: ExportSdsMetersRequest) -> ExportSdsMetersResult:
        config = await self._config_repo.get(MeterSource("sds"), request.customer_id)
        suma_color = config.suma_color if config else False

        csv_path = await self._sds_provider.export_meters_to_csv(
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            max_date=request.max_date,
            output_dir=request.output_dir,
            suma_color=suma_color,
        )

        return ExportSdsMetersResult(
            csv_path=csv_path,
            filename=Path(csv_path).name,
            customer_name=request.customer_name,
        )
