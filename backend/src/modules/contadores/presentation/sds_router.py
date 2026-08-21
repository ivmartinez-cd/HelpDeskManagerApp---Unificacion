from fastapi import APIRouter, Depends, Query
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
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores/sds", tags=["contadores-sds"])

_require_export = Depends(require_permission(EXPORT))
# El catálogo de clientes SDS lo trae completo la API del proveedor (no
# soporta paginar aguas arriba) para alimentar un combobox con búsqueda en
# vivo en el frontend — el default cubre ese catálogo completo en una sola
# página sin dejar de cumplir el contrato de paginación (ARCHITECTURE_GUIDE
# §11); un `size` explícito más chico sigue funcionando si hiciera falta.
_MAX_PAGE_SIZE = 2000


@router.get("/clients", response_model=Page[SdsClientOut])
async def list_sds_clients(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=1000, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[SdsClientOut]:
    """Obtiene la lista de clientes activos desde la API de SDS con su configuración suma_color."""
    config_repo = meter_config_repo_mod.SqlAlchemyMeterClientConfigRepository(db)
    sds_provider = HttpxSdsClientProvider()
    results = await ListSdsClientsUseCase(sds_provider, config_repo).execute()
    return Page.of([SdsClientOut.from_result(r) for r in results], page=page, size=size)


@router.put("/clients/{customer_id}/config", response_model=SdsClientOut)
async def update_sds_client_config(
    customer_id: str,
    body: UpdateSdsConfigIn,
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db, scope="function"),
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
    db: AsyncSession = Depends(get_db, scope="function"),
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
