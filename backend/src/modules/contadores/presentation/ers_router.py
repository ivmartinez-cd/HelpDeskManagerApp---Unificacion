from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.ers_dtos import ExportErsMetersRequest
from src.modules.contadores.application.use_cases.export_ers_meters import ExportErsMetersUseCase
from src.modules.contadores.application.use_cases.list_ers_clients import ListErsClientsUseCase
from src.modules.contadores.application.use_cases.update_ers_client_config import (
    UpdateErsClientConfigUseCase,
)
from src.modules.contadores.domain.well_known_permissions import EXPORT
from src.modules.contadores.infrastructure.ers.httpx_ers_client_provider import (
    HttpxErsClientProvider,
)
from src.modules.contadores.infrastructure.repositories import (
    sqlalchemy_meter_client_config_repository as meter_config_repo_mod,
)
from src.modules.contadores.presentation.schemas.ers_schemas import (
    ErsClientOut,
    ProcessErsMetersRequest,
    ProcessErsMetersResponse,
    UpdateErsConfigIn,
)
from src.modules.contadores.presentation.upload_storage import output_dir
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/contadores/ers", tags=["contadores-ers"])

_require_export = Depends(require_permission(EXPORT))


@router.get("/clients", response_model=list[ErsClientOut])
async def list_ers_clients(
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db),
) -> list[ErsClientOut]:
    """Obtiene la lista de grupos de dispositivos desde ERS con su configuración suma_color."""
    config_repo = meter_config_repo_mod.SqlAlchemyMeterClientConfigRepository(db)
    ers_provider = HttpxErsClientProvider()
    results = await ListErsClientsUseCase(ers_provider, config_repo).execute()
    return [ErsClientOut.from_result(r) for r in results]


@router.put("/clients/{customer_id}/config", response_model=ErsClientOut)
async def update_ers_client_config(
    customer_id: str,
    body: UpdateErsConfigIn,
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db),
) -> ErsClientOut:
    """Guarda/actualiza la preferencia suma_color de un grupo ERS."""
    config_repo = meter_config_repo_mod.SqlAlchemyMeterClientConfigRepository(db)
    result = await UpdateErsClientConfigUseCase(config_repo).execute(
        customer_id=customer_id,
        customer_name=body.customer_name,
        suma_color=body.suma_color,
    )
    return ErsClientOut.from_result(result)


@router.post("/process", response_model=ProcessErsMetersResponse)
async def process_ers_meters(
    body: ProcessErsMetersRequest,
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db),
) -> ProcessErsMetersResponse:
    """Obtiene los contadores de ERS para un grupo y los exporta a CSV."""
    config_repo = meter_config_repo_mod.SqlAlchemyMeterClientConfigRepository(db)
    ers_provider = HttpxErsClientProvider()
    request = ExportErsMetersRequest(
        group_id=body.customer_id,
        group_name=body.customer_name,
        max_date=body.fecha_maxima,
        output_dir=output_dir(),
    )
    result = await ExportErsMetersUseCase(ers_provider, config_repo).execute(request)
    return ProcessErsMetersResponse.from_result(result)
