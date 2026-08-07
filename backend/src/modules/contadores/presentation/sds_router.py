from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.sds_dtos import ExportSdsMetersRequest
from src.modules.contadores.application.use_cases.export_sds_meters import ExportSdsMetersUseCase
from src.modules.contadores.application.use_cases.list_sds_clients import ListSdsClientsUseCase
from src.modules.contadores.application.use_cases.update_sds_client_config import (
    UpdateSdsClientConfigUseCase,
)
from src.modules.contadores.domain.well_known_permissions import EXPORT
from src.modules.contadores.infrastructure.repositories import (
    sqlalchemy_meter_client_config_repository as meter_config_repo_mod,
)
from src.modules.contadores.infrastructure.sds.httpx_sds_client_provider import (
    HttpxSdsClientProvider,
)
from src.modules.contadores.presentation.schemas.sds_schemas import (
    ProcessSdsMetersRequest,
    ProcessSdsMetersResponse,
    SdsClientOut,
    UpdateSdsConfigIn,
)
from src.modules.contadores.presentation.upload_storage import output_dir
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/contadores/sds", tags=["contadores-sds"])

_require_export = Depends(require_permission(EXPORT))


@router.get("/clients", response_model=list[SdsClientOut])
async def list_sds_clients(
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db),
) -> list[SdsClientOut]:
    """Obtiene la lista de clientes activos desde la API de SDS con su configuración suma_color."""
    config_repo = meter_config_repo_mod.SqlAlchemyMeterClientConfigRepository(db)
    sds_provider = HttpxSdsClientProvider()
    results = await ListSdsClientsUseCase(sds_provider, config_repo).execute()
    return [SdsClientOut.from_result(r) for r in results]


@router.put("/clients/{customer_id}/config", response_model=SdsClientOut)
async def update_sds_client_config(
    customer_id: str,
    body: UpdateSdsConfigIn,
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db),
) -> SdsClientOut:
    """Guarda/actualiza la preferencia suma_color de un cliente SDS."""
    config_repo = meter_config_repo_mod.SqlAlchemyMeterClientConfigRepository(db)
    result = await UpdateSdsClientConfigUseCase(config_repo).execute(
        customer_id=customer_id,
        customer_name=body.customer_name,
        suma_color=body.suma_color,
    )
    return SdsClientOut.from_result(result)


@router.post("/process", response_model=ProcessSdsMetersResponse)
async def process_sds_meters(
    body: ProcessSdsMetersRequest,
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db),
) -> ProcessSdsMetersResponse:
    """Obtiene los contadores de SDS para un cliente y los exporta a CSV."""
    config_repo = meter_config_repo_mod.SqlAlchemyMeterClientConfigRepository(db)
    sds_provider = HttpxSdsClientProvider()
    request = ExportSdsMetersRequest(
        customer_id=body.customer_id,
        customer_name=body.customer_name,
        max_date=body.fecha_maxima,
        output_dir=output_dir(),
    )
    result = await ExportSdsMetersUseCase(sds_provider, config_repo).execute(request)
    return ProcessSdsMetersResponse.from_result(result)
