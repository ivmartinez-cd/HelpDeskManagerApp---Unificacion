"""Reporte de cierre de contadores: anexos de Impresión con el período de
facturación abierto (EN PROCESO / DEMORADO). Recrea el legacy
`SiGes/AnexosNoFacturados` con la regla de la TL — mes en curso afuera,
FACTURADO/LIBERADO/A LIBERAR afuera — y referencia que rueda sola (ver
`anexos_pendientes_query.py`). Consulta en vivo a SiGesReadOnly con caché
TTL en el gateway."""

from fastapi import APIRouter, Depends, Query

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.list_anexos_pendientes_request import (
    FiltroEstado,
    ListAnexosPendientesRequest,
)
from src.modules.contadores.application.use_cases.get_anexos_pendientes_resumen import (
    GetAnexosPendientesResumenUseCase,
)
from src.modules.contadores.application.use_cases.list_anexos_pendientes import (
    ListAnexosPendientesUseCase,
)
from src.modules.contadores.domain.well_known_permissions import VIEW
from src.modules.contadores.presentation.dependencies import get_anexos_pendientes_gateway
from src.modules.contadores.presentation.schemas.anexos_pendientes_schemas import (
    AnexoPendienteSchema,
    AnexosPendientesResumenSchema,
)
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores", tags=["contadores-anexos-pendientes"])

_require_view = Depends(require_permission(VIEW))
# El reporte se imprime entero: el default alcanza para el universo real
# (~50 filas) sin renunciar al contrato paginado (§11, catálogo chico).
_MAX_PAGE_SIZE = 500


@router.get("/anexos-pendientes", response_model=Page[AnexoPendienteSchema])
async def list_anexos_pendientes(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=200, ge=1, le=_MAX_PAGE_SIZE),
    estado: FiltroEstado = Query(default="todos"),
    search: str | None = Query(default=None, max_length=120),
    refresh: bool = Query(default=False, description="Fuerza re-consultar Siges"),
    _: Identity = _require_view,
) -> Page[AnexoPendienteSchema]:
    result = await ListAnexosPendientesUseCase(get_anexos_pendientes_gateway()).execute(
        ListAnexosPendientesRequest(estado=estado, search=search, force_refresh=refresh)
    )
    schemas = [AnexoPendienteSchema.from_anotado(a) for a in result.anexos]
    return Page.of(schemas, page=page, size=size)


@router.get("/anexos-pendientes/resumen", response_model=AnexosPendientesResumenSchema)
async def get_anexos_pendientes_resumen(
    _: Identity = _require_view,
) -> AnexosPendientesResumenSchema:
    resumen = await GetAnexosPendientesResumenUseCase(
        get_anexos_pendientes_gateway()
    ).execute()
    return AnexosPendientesResumenSchema(
        total=resumen.total,
        en_proceso=resumen.en_proceso,
        demorados=resumen.demorados,
        importe_usd_total=resumen.importe_usd_total,
        periodo_referencia=resumen.periodo_referencia,
        consultado_en=resumen.consultado_en,
    )
