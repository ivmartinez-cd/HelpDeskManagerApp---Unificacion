"""Endpoints de lectura de Insumos > Despachados: tabla, bandeja "Requieren acción",
tarjetas, estado de la actualización y detalle de una guía. Leen solo la base de HDM.

Las rutas fijas van antes de `/despachados/{guia}` a propósito."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.application.dtos.despachados import CriterioListado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    ColumnaOrden,
    OrdenDespachos,
    Pagina,
)
from src.modules.insumos.domain.well_known_permissions import VIEW
from src.modules.insumos.presentation.dependencies import (
    build_consultar_actualizacion,
    build_listar_despachos,
    build_obtener_detalle_despacho,
    build_resumir_despachos,
)
from src.modules.insumos.presentation.schemas.despachados_detalle_schemas import DetalleOut
from src.modules.insumos.presentation.schemas.despachados_schemas import (
    EstadoActualizacionOut,
    FilaDespachoOut,
    ResumenOut,
)
from src.shared.domain.errors import ValidationError
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))

PATRON_GUIA = r"^\d{19}$"
_VALORES_COLOR = frozenset(color.value for color in ColorSemaforo)
_COLORES_VALIDOS = ", ".join(color.value for color in ColorSemaforo)


def parsear_colores(texto: str) -> tuple[ColorSemaforo, ...]:
    """`rojo,naranja` -> (ROJO, NARANJA); vacío = todos. Un color desconocido es un 400
    `VALIDATION_ERROR` con la lista de válidos."""
    valores = [valor.strip().lower() for valor in texto.split(",") if valor.strip()]
    invalidos = [valor for valor in valores if valor not in _VALORES_COLOR]
    if invalidos:
        raise ValidationError(
            f"Colores inválidos: {', '.join(invalidos)} (válidos: {_COLORES_VALIDOS})"
        )
    return tuple(ColorSemaforo(valor) for valor in valores)


def orden_listado(
    orden: ColumnaOrden = Query(default=ColumnaOrden.URGENCIA),
    direccion: Literal["asc", "desc"] = Query(default="asc"),
) -> OrdenDespachos:
    """Columna por la que ordenar (`urgencia` ignora la dirección) y `asc`/`desc`. Un valor
    fuera de la lista es un 400 `VALIDATION_ERROR`."""
    return OrdenDespachos(columna=orden, descendente=direccion == "desc")


def criterio_listado(
    texto: str = Query(default="", max_length=100),
    colores: str = Query(default=""),
    operativa: str = Query(default=""),
    remito_desde: date | None = Query(default=None, alias="remitoDesde"),
    remito_hasta: date | None = Query(default=None, alias="remitoHasta"),
    orden: OrdenDespachos = Depends(orden_listado),
) -> CriterioListado:
    """Filtros y orden de la tabla desde el query string (operativa vacía = todas)."""
    return CriterioListado(
        texto=texto.strip(),
        colores=parsear_colores(colores),
        operativa=operativa.strip() or None,
        remito_desde=remito_desde,
        remito_hasta=remito_hasta,
        orden=orden,
    )


async def _pagina_de_filas(
    db: AsyncSession, criterio: CriterioListado, pagina: tuple[int, int]
) -> Page[FilaDespachoOut]:
    """Corre el listado paginado en SQL y lo envuelve en `Page[T]`."""
    page, size = pagina
    limites = Pagina(limite=size, desplazamiento=(page - 1) * size)
    listado = await build_listar_despachos(db).execute(criterio, limites)
    items = [FilaDespachoOut.from_fila(fila) for fila in listado.filas]
    return Page(items=items, total=listado.total, page=page, size=size)


@router.get("/despachados", response_model=Page[FilaDespachoOut])
async def listar_despachados(
    criterio: CriterioListado = Depends(criterio_listado),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[FilaDespachoOut]:
    """Envíos abiertos y cerrados de la ventana, rojos primero, con los filtros de la
    pantalla."""
    return await _pagina_de_filas(db, criterio, (page, size))


@router.get("/despachados/requieren-accion", response_model=Page[FilaDespachoOut])
async def listar_requieren_accion(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=500),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[FilaDespachoOut]:
    """Bandeja "Requieren acción": rojos y naranjas con la alerta abierta."""
    criterio = CriterioListado(solo_alertas_abiertas=True)
    return await _pagina_de_filas(db, criterio, (page, size))


@router.get("/despachados/resumen", response_model=ResumenOut)
async def resumen_despachados(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ResumenOut:
    """Tarjetas por color, contadores de alertas y opciones del filtro de operativa."""
    return ResumenOut.from_tarjetas(await build_resumir_despachos(db).execute())


@router.get("/despachados/actualizacion", response_model=EstadoActualizacionOut)
async def estado_actualizacion(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> EstadoActualizacionOut:
    """Si hay una corrida en curso y el resumen de la última terminada."""
    estado = await build_consultar_actualizacion(db).execute()
    return EstadoActualizacionOut.from_estado(estado)


@router.get("/despachados/{guia}", response_model=DetalleOut)
async def detalle_despacho(
    guia: str = Path(pattern=PATRON_GUIA),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DetalleOut:
    """Envío con su estado de OCA, remitos con incidentes, cambios observados y acciones."""
    detalle = await build_obtener_detalle_despacho(db).execute(guia)
    return DetalleOut.from_detalle(detalle)
