"""Cruce clientes de Gestión ↔ empresas de Siges para la card de Inicio:
resumen por operador, búsqueda de empresas y mapeo manual."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.use_cases.filtrar_pendientes_periodo_por_operador import (
    FiltrarPendientesPeriodoPorOperador,
)
from src.modules.contadores.application.use_cases.get_clientes_pendientes_periodo import (
    GetClientesPendientesPeriodo,
)
from src.modules.contadores.application.use_cases.get_resumen_clientes_operador import (
    GetResumenClientesOperador,
    GetResumenClientesOperadorDependencies,
)
from src.modules.contadores.application.use_cases.resolver_cliente_siges import (
    SearchEmpresasSiges,
    SetClienteSigesMap,
    SetClienteSigesMapCommand,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_cliente_siges_map_repository import (  # noqa: E501
    SqlAlchemyClienteSigesMapRepository,
)
from src.modules.contadores.presentation.calendario_routers._deps import (
    DEFAULT_SYNC_WINDOW_DAYS,
    POOL_BACKLOG_OPERADOR_IDS,
    require_manage,
    require_view,
)
from src.modules.contadores.presentation.dependencies import (
    get_clientes_pendientes_periodo_gateway_or_none,
    get_parque_cliente_gateway,
    get_parque_cliente_gateway_or_none,
)
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    ClientesPendientesPeriodoResponse,
    EmpresaSigesSchema,
    ResumenClientesOperadorResponse,
    SetClienteSigesMapRequest,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/calendario/resumen-clientes", response_model=ResumenClientesOperadorResponse)
async def get_resumen_clientes_operador(
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ResumenClientesOperadorResponse:
    """Card de Inicio: cartera de clientes por operador (ventana futura del
    calendario — la misma que sincroniza el sync, ver el docstring del use
    case) e impresoras cruzadas contra Siges por nombre. Los operadores pool
    se excluyen igual que en el backlog de pendientes. Un operador regular ve
    solo su propia cartera; el superadmin ve el desglose de todos."""
    deps = GetResumenClientesOperadorDependencies(
        calendar=SqlAlchemyCalendarEventRepository(db),
        alias=SqlAlchemyClienteSigesMapRepository(db),
        parque=get_parque_cliente_gateway_or_none(),
    )
    dto = await GetResumenClientesOperador(deps).execute(
        hoy=datetime.now(UTC).date(),
        dias_ventana=DEFAULT_SYNC_WINDOW_DAYS,
        is_superadmin=identity.user.is_superadmin,
        full_name=identity.user.full_name,
        exclude_operador_ids=POOL_BACKLOG_OPERADOR_IDS,
    )
    return ResumenClientesOperadorResponse.model_validate(dto)


@router.get(
    "/calendario/pendientes-periodo-anterior",
    response_model=ClientesPendientesPeriodoResponse,
)
async def get_clientes_pendientes_periodo_anterior(
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ClientesPendientesPeriodoResponse:
    """Card de Inicio: arrastre real del cierre que acaba de pasar (clientes
    con anexo de Impresión pendiente de exactamente el período inmediato
    anterior), sin depender del backlog de calendario de Gestión. Recortado a
    la cartera del operador (el superadmin ve todos) — ver
    FiltrarPendientesPeriodoPorOperador."""
    gateway = get_clientes_pendientes_periodo_gateway_or_none()
    resultado = None if gateway is None else await GetClientesPendientesPeriodo(gateway).execute()
    if resultado is None:
        return ClientesPendientesPeriodoResponse(periodo=None, cantidad=None, grupos=None)
    repo = SqlAlchemyCalendarEventRepository(db)
    resultado = await FiltrarPendientesPeriodoPorOperador(repo).execute(
        resultado,
        is_superadmin=identity.user.is_superadmin,
        full_name=identity.user.full_name,
        hoy=datetime.now(UTC).date(),
        dias_ventana=DEFAULT_SYNC_WINDOW_DAYS,
    )
    return ClientesPendientesPeriodoResponse(
        periodo=resultado.periodo,
        cantidad=resultado.cantidad,
        grupos=list(resultado.grupos),
    )


@router.get("/calendario/empresas-siges", response_model=Page[EmpresaSigesSchema])
async def search_empresas_siges(
    q: str = Query(..., min_length=2, description="Texto a buscar en Den_Comercial"),
    _: Identity = require_manage,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=50),
) -> Page[EmpresaSigesSchema]:
    """Búsqueda en vivo de empresas activas en Siges (con su parque) para
    resolver un cliente sin cruce desde la card de Inicio."""
    empresas = await SearchEmpresasSiges(get_parque_cliente_gateway()).execute(q)
    return Page.of(
        [EmpresaSigesSchema.model_validate(e) for e in empresas], page=page, size=size
    )


@router.put("/calendario/cliente-siges-map", status_code=status.HTTP_204_NO_CONTENT)
async def set_cliente_siges_map(
    payload: SetClienteSigesMapRequest,
    _: Identity = require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    """Reemplaza el mapeo manual de un cliente de Gestión a empresa(s) de
    Siges (lista vacía = desmapear). El cruce automático queda para los que
    matchean solos; esto es solo para los nombres rebeldes."""
    await SetClienteSigesMap(SqlAlchemyClienteSigesMapRepository(db)).execute(
        SetClienteSigesMapCommand(
            cliente_gestion=payload.cliente_gestion,
            siges_empresa_ids=payload.siges_empresa_ids,
        )
    )
