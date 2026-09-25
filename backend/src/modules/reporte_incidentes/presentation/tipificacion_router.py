from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.reporte_incidentes.application.use_cases.armar_reporte import PedidoReporte
from src.modules.reporte_incidentes.application.use_cases.gestionar_tipificacion import (
    Correccion,
)
from src.modules.reporte_incidentes.domain.entities.categoria import Categoria
from src.modules.reporte_incidentes.domain.well_known_permissions import UPDATE, VIEW
from src.modules.reporte_incidentes.presentation.dependencies import (
    build_corregir_tipificacion,
    build_eliminar_categoria,
    build_guardar_categoria,
    build_taxonomia,
    build_tipificar_pendientes,
)
from src.modules.reporte_incidentes.presentation.query_params import pedido_reporte
from src.modules.reporte_incidentes.presentation.schemas.tipificacion_schemas import (
    CategoriaDetalleSchema,
    CategoriaRequest,
    CorreccionRequest,
    ResultadoIASchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/reporte-incidentes", tags=["reporte-incidentes"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_db = Depends(get_db, scope="function")


def _categoria(body: CategoriaRequest) -> Categoria:
    return Categoria(body.nombre, body.color, body.descripcion, tuple(body.subcategorias))


@router.post("/tipificar", response_model=ResultadoIASchema)
async def tipificar_pendientes(
    pedido: PedidoReporte = Depends(pedido_reporte),
    _: Identity = _require_update,
    db: AsyncSession = _db,
) -> ResultadoIASchema:
    """Tipifica con IA los casos del rango sin tipificación guardada (cuesta dinero)."""
    resultado = await build_tipificar_pendientes(db).execute(pedido)
    return ResultadoIASchema.model_validate(resultado)


@router.put("/tipificacion", status_code=status.HTTP_204_NO_CONTENT)
async def corregir_tipificacion(
    body: CorreccionRequest, _: Identity = _require_update, db: AsyncSession = _db
) -> None:
    """Corrección manual: queda guardada con confianza alta para ese contenido."""
    await build_corregir_tipificacion(db).execute(Correccion(**body.model_dump()))


@router.get("/categorias", response_model=Page[CategoriaDetalleSchema])
async def listar_categorias(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=200),
    _: Identity = _require_view,
    db: AsyncSession = _db,
) -> Page[CategoriaDetalleSchema]:
    categorias = await build_taxonomia(db).listar()
    items = [CategoriaDetalleSchema.model_validate(c) for c in categorias]
    return Page.of(items, page=page, size=size)


@router.post("/categorias", status_code=status.HTTP_201_CREATED)
async def crear_categoria(
    body: CategoriaRequest, _: Identity = _require_update, db: AsyncSession = _db
) -> None:
    await build_guardar_categoria(db).execute(_categoria(body), nombre_anterior=None)


@router.put("/categorias/{nombre}", status_code=status.HTTP_204_NO_CONTENT)
async def editar_categoria(
    nombre: str, body: CategoriaRequest, _: Identity = _require_update, db: AsyncSession = _db
) -> None:
    await build_guardar_categoria(db).execute(_categoria(body), nombre_anterior=nombre)


@router.delete("/categorias/{nombre}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_categoria(
    nombre: str, _: Identity = _require_update, db: AsyncSession = _db
) -> None:
    await build_eliminar_categoria(db).execute(nombre)
