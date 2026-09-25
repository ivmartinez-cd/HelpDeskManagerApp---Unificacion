import unicodedata
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.reporte_incidentes.application.use_cases.armar_reporte import PedidoReporte
from src.modules.reporte_incidentes.application.use_cases.vista_reporte import (
    CampoOrden,
    buscar,
    componer_vista,
    ordenar,
    pendientes_de_revision,
)
from src.modules.reporte_incidentes.domain.entities.incidente import Empresa
from src.modules.reporte_incidentes.domain.services.filtros import (
    Filtros,
    aplicar_filtros,
    opciones_filtro,
    sanear_filtros,
)
from src.modules.reporte_incidentes.domain.well_known_permissions import VIEW
from src.modules.reporte_incidentes.presentation.dependencies import (
    build_armar_reporte,
    get_incidentes_gateway,
)
from src.modules.reporte_incidentes.presentation.mappers import a_respuesta
from src.modules.reporte_incidentes.presentation.schemas.reporte_schemas import (
    EmpresaSchema,
    IncidenteSchema,
    ReporteResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/reporte-incidentes", tags=["reporte-incidentes"])

_require_view = Depends(require_permission(VIEW))
_db = Depends(get_db, scope="function")
# La tabla muestra 50 por página (como el legacy); el tope cubre el reporte
# imprimible y un rango largo de un cliente chico.
_MAX_PAGE_SIZE = 500


def pedido_reporte(
    empresa_id: str = Query(..., min_length=1),
    periodo: str | None = Query(None, description="Mes final AAAA-MM (default: el actual)"),
    meses: int | None = Query(None, description="Cantidad de meses del rango (1 a 24)"),
) -> PedidoReporte:
    return PedidoReporte(empresa_id=empresa_id, periodo=periodo, meses=meses)


def filtros_crudos(sucursal: str = "", categoria: str = "", subcategoria: str = "") -> Filtros:
    return Filtros(sucursal=sucursal, categoria=categoria, subcategoria=subcategoria)


def _plano(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def _coincide(empresa: Empresa, q: str) -> bool:
    return not q or q in _plano(empresa.nombre) or q in empresa.id


@router.get("/empresas", response_model=Page[EmpresaSchema])
async def listar_empresas(
    q: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
) -> Page[EmpresaSchema]:
    """Clientes activos, buscables por nombre (sin acentos) o id."""
    empresas = await get_incidentes_gateway().listar_empresas()
    buscado = _plano(q.strip())
    items = [EmpresaSchema.model_validate(e) for e in empresas if _coincide(e, buscado)]
    return Page.of(items, page=page, size=size)


@router.get("/reporte", response_model=ReporteResponse)
async def obtener_reporte(
    pedido: PedidoReporte = Depends(pedido_reporte),
    filtros: Filtros = Depends(filtros_crudos),
    _: Identity = _require_view,
    db: AsyncSession = _db,
) -> ReporteResponse:
    """KPIs, gráficos, oportunidades de mejora y opciones de filtro del rango."""
    reporte = await build_armar_reporte(db).execute(pedido)
    return a_respuesta(componer_vista(reporte, filtros))


@router.get("/incidentes", response_model=Page[IncidenteSchema])
async def listar_incidentes(
    pedido: PedidoReporte = Depends(pedido_reporte),
    filtros: Filtros = Depends(filtros_crudos),
    q: str = "",
    orden: CampoOrden | None = None,
    direccion: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
    db: AsyncSession = _db,
) -> Page[IncidenteSchema]:
    """Incidentes de la selección filtrada, con búsqueda y orden por columna."""
    incidentes = (await build_armar_reporte(db).execute(pedido)).incidentes
    saneados = sanear_filtros(filtros, opciones_filtro(incidentes))
    seleccion = buscar(aplicar_filtros(incidentes, saneados), q)
    items = ordenar(seleccion, orden, direccion == "desc")
    return Page.of([IncidenteSchema.model_validate(i) for i in items], page=page, size=size)


@router.get("/pendientes", response_model=Page[IncidenteSchema])
async def listar_pendientes(
    pedido: PedidoReporte = Depends(pedido_reporte),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
    db: AsyncSession = _db,
) -> Page[IncidenteSchema]:
    """"Pendiente de revision" del período completo (panel de revisión manual)."""
    reporte = await build_armar_reporte(db).execute(pedido)
    items = [IncidenteSchema.model_validate(i) for i in pendientes_de_revision(reporte)]
    return Page.of(items, page=page, size=size)
