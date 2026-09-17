"""Reporte "Detalle de contadores por nro de proceso" — reconstrucción en
vivo del reporte legacy SSRS (ver `falta_contador_proceso_query.py` para la
investigación de origen), con el proceso completo en vez de solo las filas
con falta de contador.

Dos endpoints con permisos distintos: ver el reporte en pantalla (`VIEW`,
no genera nada) y exportarlo a XLSX para mandarle al cliente (`EXPORT`,
mismo criterio que `tools_router.py`: generar un archivo para llevarse es
una acción de exportación, no de simple lectura)."""

import io
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.use_cases.generar_reporte_xlsx_detalle_proceso import (
    GenerarReporteXlsxDetalleProcesoUseCase,
)
from src.modules.contadores.application.use_cases.get_detalle_contador_por_grupo import (
    GetDetalleContadorPorGrupoUseCase,
)
from src.modules.contadores.application.use_cases.get_detalle_contador_proceso import (
    GetDetalleContadorProcesoUseCase,
)
from src.modules.contadores.domain.well_known_permissions import EXPORT, VIEW
from src.modules.contadores.infrastructure.xlsx.openpyxl_detalle_contador_writer import (
    OpenpyxlDetalleContadorWriter,
)
from src.modules.contadores.presentation.dependencies import (
    get_detalle_contador_proceso_gateway,
)
from src.modules.contadores.presentation.schemas.detalle_contador_proceso_schemas import (
    DetalleContadorProcesoSchema,
)

router = APIRouter(prefix="/api/contadores/detalle-proceso", tags=["contadores-detalle-proceso"])

_require_view = Depends(require_permission(VIEW))
_require_export = Depends(require_permission(EXPORT))
_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/por-grupo/{id_grupo_economico}")
async def get_detalle_contador_por_grupo(
    id_grupo_economico: int, _: Identity = _require_view
) -> DetalleContadorProcesoSchema:
    """Trae de una sola vez todos los procesos/anexos recientes del cliente
    (pedido del usuario: elegir cliente ya trae todo el parque, el selector
    de Proceso queda como filtro opcional sobre lo ya cargado)."""
    use_case = GetDetalleContadorPorGrupoUseCase(get_detalle_contador_proceso_gateway())
    resultado = await use_case.execute(id_grupo_economico)
    return DetalleContadorProcesoSchema.from_domain(resultado)


@router.get("/{nro_proceso}")
async def get_detalle_contador_proceso(
    nro_proceso: int, _: Identity = _require_view
) -> DetalleContadorProcesoSchema:
    use_case = GetDetalleContadorProcesoUseCase(get_detalle_contador_proceso_gateway())
    resultado = await use_case.execute(nro_proceso)
    return DetalleContadorProcesoSchema.from_domain(resultado)


@router.get("/{nro_proceso}/xlsx")
async def get_detalle_contador_proceso_xlsx(
    nro_proceso: int,
    alcance: Literal["todos", "falta_contador"] = "todos",
    _: Identity = _require_export,
) -> StreamingResponse:
    """Reporte ejecutivo XLSX con las mismas columnas de la pantalla (pedido
    explícito del usuario), acotado al `alcance` que tenía tildado la
    pantalla (todo el proceso o solo falta contador)."""
    use_case = GenerarReporteXlsxDetalleProcesoUseCase(
        get_detalle_contador_proceso_gateway(), OpenpyxlDetalleContadorWriter()
    )
    reporte = await use_case.execute(nro_proceso, alcance)
    return StreamingResponse(
        io.BytesIO(reporte.contenido),
        media_type=_XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{reporte.filename}"'},
    )
