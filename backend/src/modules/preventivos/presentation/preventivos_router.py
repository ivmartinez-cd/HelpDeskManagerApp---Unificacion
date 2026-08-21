"""Preventivos por zona de distribución: parque local con vencimiento
calculado y habilitación local (v1: solo marca en esta app, sin escribir en
Gestión/Siges — ver ADR del módulo). Visibilidad sin filtro por operador: las
zonas son geografía local, no cartera de PST."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.preventivos.application.dtos.habilitar_request import (
    DeshabilitarEquipoRequest,
    HabilitarEquipoRequest,
)
from src.modules.preventivos.application.dtos.list_equipos_request import (
    ListEquiposPorZonaRequest,
)
from src.modules.preventivos.application.use_cases.deshabilitar_equipo import (
    DeshabilitarEquipoUseCase,
)
from src.modules.preventivos.application.use_cases.habilitar_equipo import (
    HabilitarEquipoUseCase,
)
from src.modules.preventivos.application.use_cases.list_equipos_por_zona import (
    ListEquiposPorZonaDependencies,
    ListEquiposPorZonaUseCase,
)
from src.modules.preventivos.application.use_cases.list_zonas import (
    ListZonasDependencies,
    ListZonasUseCase,
)
from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)
from src.modules.preventivos.domain.well_known_permissions import UPDATE, VIEW
from src.modules.preventivos.infrastructure.repositories.sqlalchemy_habilitacion_repository import (  # noqa: E501
    SqlAlchemyHabilitacionRepository,
)
from src.modules.preventivos.presentation.dependencies import (
    get_preventivos_gateway,
    get_zonas_excluidas,
)
from src.modules.preventivos.presentation.schemas.preventivos_schemas import (
    EquipoPreventivoSchema,
    EquiposPreventivosPage,
    HabilitacionSchema,
    HabilitarEquipoBody,
    ZonaSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/preventivos", tags=["preventivos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_MAX_PAGE_SIZE = 500


@router.get("/zonas", response_model=Page[ZonaSchema])
async def list_zonas(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
) -> Page[ZonaSchema]:
    use_case = ListZonasUseCase(
        ListZonasDependencies(
            gateway=get_preventivos_gateway(), zonas_excluidas=get_zonas_excluidas()
        )
    )
    zonas = await use_case.execute()
    return Page.of([ZonaSchema.from_domain(z) for z in zonas], page=page, size=size)


@router.get("/equipos", response_model=EquiposPreventivosPage)
async def list_equipos(
    zona: str = Query(min_length=1, max_length=20),
    estado: EstadoPreventivo | None = Query(default=None),
    habilitado: bool | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    refresh: bool = Query(default=False, description="Fuerza re-consultar Siges"),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> EquiposPreventivosPage:
    use_case = ListEquiposPorZonaUseCase(
        ListEquiposPorZonaDependencies(
            gateway=get_preventivos_gateway(),
            habilitaciones=SqlAlchemyHabilitacionRepository(db),
            zonas_excluidas=get_zonas_excluidas(),
        )
    )
    result = await use_case.execute(
        ListEquiposPorZonaRequest(
            zona=zona, estado=estado, habilitado=habilitado, search=q, force_refresh=refresh
        )
    )
    schemas = [EquipoPreventivoSchema.from_anotado(a) for a in result.equipos]
    base = Page.of(schemas, page=page, size=size)
    return EquiposPreventivosPage(
        items=base.items,
        total=base.total,
        page=base.page,
        size=base.size,
        consultado_en=result.consultado_en,
    )


@router.post(
    "/equipos/{siges_maquina_id}/habilitar",
    response_model=HabilitacionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def habilitar_equipo(
    siges_maquina_id: int,
    body: HabilitarEquipoBody,
    identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> HabilitacionSchema:
    info = await HabilitarEquipoUseCase(SqlAlchemyHabilitacionRepository(db)).execute(
        HabilitarEquipoRequest(
            siges_maquina_id=siges_maquina_id,
            habilitado_por_user_id=identity.user.id,
            habilitado_por_nombre=identity.user.full_name,
            nota=body.nota,
        )
    )
    return HabilitacionSchema.from_info(info)


@router.delete("/equipos/{siges_maquina_id}/habilitar", status_code=status.HTTP_204_NO_CONTENT)
async def deshabilitar_equipo(
    siges_maquina_id: int,
    identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Response:
    await DeshabilitarEquipoUseCase(SqlAlchemyHabilitacionRepository(db)).execute(
        DeshabilitarEquipoRequest(
            siges_maquina_id=siges_maquina_id,
            deshabilitado_por_nombre=identity.user.full_name,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
