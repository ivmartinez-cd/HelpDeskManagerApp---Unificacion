import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.prestadores.application.dtos.prestador_dtos import (
    AssignOperadorCommand,
    CreatePrestadorCommand,
    SetPrestadorActiveCommand,
    UpdatePrestadorCommand,
)
from src.modules.prestadores.application.use_cases.assign_operador import (
    AssignOperador,
    AssignOperadorDependencies,
)
from src.modules.prestadores.application.use_cases.create_prestador import (
    CreatePrestador,
    CreatePrestadorDependencies,
)
from src.modules.prestadores.application.use_cases.deactivate_prestador import (
    SetPrestadorActive,
    SetPrestadorActiveDependencies,
)
from src.modules.prestadores.application.use_cases.get_prestador import (
    GetPrestador,
    GetPrestadorDependencies,
)
from src.modules.prestadores.application.use_cases.list_asignacion_historial import (
    ListAsignacionHistorial,
    ListAsignacionHistorialDependencies,
)
from src.modules.prestadores.application.use_cases.list_prestadores_agrupados import (
    ListPrestadoresAgrupados,
    ListPrestadoresAgrupadosDependencies,
)
from src.modules.prestadores.application.use_cases.sync_prestadores_desde_siges import (
    SyncPrestadoresDesdeSiges,
    SyncPrestadoresDesdeSigesDependencies,
)
from src.modules.prestadores.application.use_cases.update_prestador import (
    UpdatePrestador,
    UpdatePrestadorDependencies,
)
from src.modules.prestadores.domain.well_known_permissions import CREATE, UPDATE, VIEW
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_asignacion_historial_repository import (  # noqa: E501
    SqlAlchemyAsignacionHistorialRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_contacto_repository import (
    SqlAlchemyContactoRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.prestadores.presentation.contactos_router import router as contactos_router
from src.modules.prestadores.presentation.dependencies import get_prestador_siges_gateway
from src.modules.prestadores.presentation.overrides_router import router as overrides_router
from src.modules.prestadores.presentation.schemas.prestador_schemas import (
    AsignacionHistorialResponse,
    AssignOperadorRequest,
    CreatePrestadorRequest,
    OperadorOptionResponse,
    PrestadoresResumenResponse,
    PrestadorResponse,
    SetActiveRequest,
    SyncResultResponse,
    UpdatePrestadorRequest,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/prestadores", tags=["prestadores"])

_require_view = Depends(require_permission(VIEW))
_require_create = Depends(require_permission(CREATE))
_require_update = Depends(require_permission(UPDATE))
# Catálogo chico (~24 PST hoy); default generoso porque alimenta el listado
# agrupado completo, no una tabla paginada en la UI (mismo criterio que
# turnos/contadores para catálogos chicos).
_DEFAULT_SIZE = 200

# Incluido acá arriba, antes de registrar `/{prestador_id}` — de lo contrario
# Starlette matchea `/overrides` contra ese catch-all de 1 segmento primero
# (mismo motivo por el que `/operadores` está definido antes de
# `/{prestador_id}` más abajo) y nunca llega a este router.
router.include_router(overrides_router)


@router.get("")
async def list_prestadores(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> PrestadoresResumenResponse:
    deps = ListPrestadoresAgrupadosDependencies(
        prestadores=SqlAlchemyPrestadorRepository(db),
        contactos=SqlAlchemyContactoRepository(db),
        users=SqlAlchemyUserProvider(db),
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
    )
    resumen = await ListPrestadoresAgrupados(deps).execute()
    return PrestadoresResumenResponse.from_dto(resumen)


@router.get("/operadores")
async def list_operadores(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[OperadorOptionResponse]:
    users = await SqlAlchemyUserProvider(db).list_all_active_users()
    return Page.of(
        [OperadorOptionResponse.from_info(u) for u in users], page=page, size=size
    )


@router.post("/sync", response_model=SyncResultResponse)
async def sync_desde_siges(
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SyncResultResponse:
    """Actualiza razón social/denominación/CUIT de los PST ya conocidos desde
    Siges. No crea ni desactiva PST — eso es siempre una acción explícita."""
    deps = SyncPrestadoresDesdeSigesDependencies(
        prestadores=SqlAlchemyPrestadorRepository(db),
        siges=get_prestador_siges_gateway(),
    )
    result = await SyncPrestadoresDesdeSiges(deps).execute()
    return SyncResultResponse.from_dto(result)


@router.get("/{prestador_id}")
async def get_prestador(
    prestador_id: uuid.UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> PrestadorResponse:
    deps = GetPrestadorDependencies(
        prestadores=SqlAlchemyPrestadorRepository(db),
        contactos=SqlAlchemyContactoRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    dto = await GetPrestador(deps).execute(prestador_id)
    return PrestadorResponse.from_dto(dto)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_prestador(
    payload: CreatePrestadorRequest,
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db),
) -> PrestadorResponse:
    deps = CreatePrestadorDependencies(
        prestadores=SqlAlchemyPrestadorRepository(db),
        asignaciones=SqlAlchemyAsignacionHistorialRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    dto = await CreatePrestador(deps).execute(
        CreatePrestadorCommand(
            siges_empresa_id=payload.siges_empresa_id,
            den_comercial=payload.den_comercial,
            razon_social=payload.razon_social,
            cuit=payload.cuit,
            equipos=payload.equipos,
            operador_id=payload.operador_id,
        )
    )
    return PrestadorResponse.from_dto(dto)


@router.put("/{prestador_id}")
async def update_prestador(
    prestador_id: uuid.UUID,
    payload: UpdatePrestadorRequest,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorResponse:
    deps = UpdatePrestadorDependencies(
        prestadores=SqlAlchemyPrestadorRepository(db),
        contactos=SqlAlchemyContactoRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    dto = await UpdatePrestador(deps).execute(
        UpdatePrestadorCommand(
            prestador_id=prestador_id,
            den_comercial=payload.den_comercial,
            razon_social=payload.razon_social,
            cuit=payload.cuit,
            equipos=payload.equipos,
        )
    )
    return PrestadorResponse.from_dto(dto)


@router.post("/{prestador_id}/activo", status_code=status.HTTP_204_NO_CONTENT)
async def set_prestador_active(
    prestador_id: uuid.UUID,
    payload: SetActiveRequest,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    deps = SetPrestadorActiveDependencies(prestadores=SqlAlchemyPrestadorRepository(db))
    await SetPrestadorActive(deps).execute(
        SetPrestadorActiveCommand(prestador_id=prestador_id, is_active=payload.is_active)
    )


@router.post("/{prestador_id}/operador")
async def assign_operador(
    prestador_id: uuid.UUID,
    payload: AssignOperadorRequest,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorResponse:
    deps = AssignOperadorDependencies(
        prestadores=SqlAlchemyPrestadorRepository(db),
        asignaciones=SqlAlchemyAsignacionHistorialRepository(db),
        contactos=SqlAlchemyContactoRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    dto = await AssignOperador(deps).execute(
        AssignOperadorCommand(
            prestador_id=prestador_id, operador_id=payload.operador_id, desde=payload.desde
        )
    )
    return PrestadorResponse.from_dto(dto)


@router.get("/{prestador_id}/historial")
async def list_historial(
    prestador_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[AsignacionHistorialResponse]:
    deps = ListAsignacionHistorialDependencies(
        asignaciones=SqlAlchemyAsignacionHistorialRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    items = await ListAsignacionHistorial(deps).execute(prestador_id)
    return Page.of(
        [AsignacionHistorialResponse.from_dto(i) for i in items], page=page, size=size
    )


router.include_router(contactos_router)
