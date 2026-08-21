"""Análisis de equipos sin contador real (migra el reporte legacy
`sitesphp/.../EquiposSinContadorReal` a un ítem propio de Contadores).
Consulta en vivo a SiGesReadOnly con caché TTL en el gateway — ver
`get_equipos_sin_real_gateway` para el porqué de los tiempos. Cada fila se
anota con el operador asignado al cliente (calendario local + cruce con
Siges, la cadena inversa de la card de Inicio)."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.list_equipos_sin_real_request import (
    ListEquiposSinRealRequest,
)
from src.modules.contadores.application.use_cases.get_equipos_sin_real_resumen import (
    GetEquiposSinRealResumenUseCase,
)
from src.modules.contadores.application.use_cases.list_equipos_sin_real import (
    ListEquiposSinRealDependencies,
    ListEquiposSinRealUseCase,
)
from src.modules.contadores.application.use_cases.operador_por_empresa import (
    MapaOperadorPorEmpresa,
)
from src.modules.contadores.domain.well_known_permissions import VIEW
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_cliente_siges_map_repository import (  # noqa: E501
    SqlAlchemyClienteSigesMapRepository,
)
from src.modules.contadores.presentation.dependencies import (
    get_equipos_sin_real_gateway,
    get_parque_cliente_gateway_or_none,
)
from src.modules.contadores.presentation.schemas.equipos_sin_real_schemas import (
    EquipoSinRealSchema,
    EquiposSinRealResumenSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores", tags=["contadores-equipos-sin-real"])

_require_view = Depends(require_permission(VIEW))
_MAX_PAGE_SIZE = 500


def _operador_mapa(db: AsyncSession) -> MapaOperadorPorEmpresa | None:
    parque = get_parque_cliente_gateway_or_none()
    if parque is None:
        return None
    return MapaOperadorPorEmpresa(
        calendar=SqlAlchemyCalendarEventRepository(db),
        alias=SqlAlchemyClienteSigesMapRepository(db),
        parque=parque,
    )


@router.get("/equipos-sin-real", response_model=Page[EquipoSinRealSchema])
async def list_equipos_sin_real(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    sort_by: Literal["meses", "cliente", "sucursal", "modelo", "operador"] = Query(
        default="meses"
    ),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    min_meses: int = Query(default=3, ge=1),
    search: str | None = Query(default=None, max_length=120),
    refresh: bool = Query(default=False, description="Fuerza re-consultar Siges (~10s)"),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[EquipoSinRealSchema]:
    deps = ListEquiposSinRealDependencies(
        port=get_equipos_sin_real_gateway(), operador_mapa=_operador_mapa(db)
    )
    result = await ListEquiposSinRealUseCase(deps).execute(
        ListEquiposSinRealRequest(
            min_meses=min_meses,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
            force_refresh=refresh,
        )
    )
    schemas = [EquipoSinRealSchema.from_anotado(a) for a in result.equipos]
    return Page.of(schemas, page=page, size=size)


@router.get("/equipos-sin-real/resumen", response_model=EquiposSinRealResumenSchema)
async def get_equipos_sin_real_resumen(
    _: Identity = _require_view,
) -> EquiposSinRealResumenSchema:
    use_case = GetEquiposSinRealResumenUseCase(get_equipos_sin_real_gateway())
    resumen = await use_case.execute()
    return EquiposSinRealResumenSchema(
        total=resumen.total,
        criticos=resumen.criticos,
        altos=resumen.altos,
        medios=resumen.medios,
        bajos=resumen.bajos,
        nunca_real=resumen.nunca_real,
        consultado_en=resumen.consultado_en,
    )
