"""Herramienta Proyección (Estimador de Contadores v1.7) — combos, grilla y
candidatos contra Siges real (`SiGesReadOnly`). Sin selección real de
grupo/proceso, `/tablero` devuelve el tablero de ejemplo (ver
`infrastructure/ejemplo/datos_ejemplo_proyeccion.py`). Los endpoints de
candidatos y de recesos viven en `proyeccion_candidatos_router.py` y
`proyeccion_recesos_router.py` (mismo prefix, incluidos al final de este
archivo) para no pasar el máximo de 300 líneas."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.features import require_feature_or_permission
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.decision_operador_dto import (
    SolicitudRestauracionDto,
)
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases.generar_export_csv import (
    GenerarExportCsvUseCase,
    OpcionesExportCsv,
)
from src.modules.contadores.application.use_cases.get_tablero_proyeccion import (
    GetTableroProyeccionUseCase,
)
from src.modules.contadores.application.use_cases.get_tablero_proyeccion_siges import (
    GetTableroProyeccionSigesUseCase,
)
from src.modules.contadores.application.use_cases.list_anexos_por_grupo_estimacion import (
    ListAnexosPorGrupoEstimacionUseCase,
)
from src.modules.contadores.application.use_cases.list_grupos_economicos_estimacion import (
    ListGruposEconomicosEstimacionUseCase,
)
from src.modules.contadores.application.use_cases.list_procesos_por_grupo_estimacion import (
    ListProcesosPorGrupoEstimacionUseCase,
)
from src.modules.contadores.domain.services.estimacion.codificacion_cp1252 import (
    codificar_cp1252,
)
from src.modules.contadores.domain.well_known_features import PROYECCION_OPERAR
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    NRO_PROCESO_EJEMPLO,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    get_decisiones_operador_store,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_decisiones_operador_repository import (  # noqa: E501
    SqlAlchemyDecisionesOperadorRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_estim_log_repository import (
    SqlAlchemyEstimLogRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_recesos_repository import (
    SqlAlchemyRecesosRepository,
)
from src.modules.contadores.presentation._proyeccion_contexto_ejemplo import contexto_ejemplo
from src.modules.contadores.presentation._proyeccion_solicitud_real import operador_de
from src.modules.contadores.presentation.dependencies import (
    get_candidatos_equipo_gateway,
    get_grilla_estimacion_gateway,
    get_proceso_estimacion_gateway,
)
from src.modules.contadores.presentation.proyeccion_candidatos_router import (
    router as candidatos_router,
)
from src.modules.contadores.presentation.proyeccion_historial_router import (
    router as historial_router,
)
from src.modules.contadores.presentation.proyeccion_recesos_router import (
    router as recesos_router,
)
from src.modules.contadores.presentation.schemas.proyeccion_schemas import (
    AnexoOptionSchema,
    GrupoEconomicoOptionSchema,
    ProcesoOptionSchema,
    TableroProyeccionSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores/proyeccion", tags=["contadores-proyeccion"])

_require_view = Depends(require_permission(VIEW))
# Exportar alcanza con el mismo permiso que opera la grilla (el legacy no
# separa quién decide de quién exporta).
_require_operar = Depends(require_feature_or_permission(PROYECCION_OPERAR, MANAGE))
_TAMANIO_PAGINA_CATALOGO_CHICO = 50


def _pagina_completa[T](items: list[T]) -> Page[T]:
    """Estos combos no tienen paginación en la UI (búsqueda en vivo sobre la
    lista ya traída, ARCHITECTURE_GUIDE.md §11) — `size` fijo en 50 truncaba
    en silencio catálogos reales con más de 50 filas (ej. grupos económicos
    con Siges en producción). `size` nunca por debajo del piso, para no
    romper metadata de clientes que lo lean, pero jamás corta `items`."""
    return Page.of(items, page=1, size=max(len(items), _TAMANIO_PAGINA_CATALOGO_CHICO))


@router.get("/grupos-economicos", response_model=Page[GrupoEconomicoOptionSchema])
async def list_grupos_economicos(
    _: Identity = _require_view,
) -> Page[GrupoEconomicoOptionSchema]:
    """Combo real contra Siges (MODELO_DE_DATOS.md §3.1) — el resto del
    tablero (`/tablero`) todavía usa datos de ejemplo, ver docstring del
    módulo."""
    grupos = await ListGruposEconomicosEstimacionUseCase(get_proceso_estimacion_gateway()).execute()
    items = [GrupoEconomicoOptionSchema.model_validate(g) for g in grupos]
    return _pagina_completa(items)


@router.get("/procesos", response_model=Page[ProcesoOptionSchema])
async def list_procesos(
    id_grupo_economico: int, _: Identity = _require_view
) -> Page[ProcesoOptionSchema]:
    """Combo real contra Siges (MODELO_DE_DATOS.md §3.2), en cascada tras
    elegir un grupo económico."""
    use_case = ListProcesosPorGrupoEstimacionUseCase(get_proceso_estimacion_gateway())
    procesos = await use_case.execute(id_grupo_economico)
    items = [ProcesoOptionSchema.model_validate(p) for p in procesos]
    return _pagina_completa(items)


@router.get("/anexos", response_model=Page[AnexoOptionSchema])
async def list_anexos(
    id_grupo_economico: int, _: Identity = _require_view
) -> Page[AnexoOptionSchema]:
    """Combo real contra Siges (MODELO_DE_DATOS.md §3.3) — acota el alcance
    de un receso a un anexo puntual en vez de todo el grupo."""
    use_case = ListAnexosPorGrupoEstimacionUseCase(get_proceso_estimacion_gateway())
    anexos = await use_case.execute(id_grupo_economico)
    items = [AnexoOptionSchema.model_validate(a) for a in anexos]
    return _pagina_completa(items)


@router.get("/tablero", response_model=TableroProyeccionSchema)
async def get_tablero(
    fecha_objetivo: date | None = None,
    nro_proceso: int | None = None,
    id_grupo_economico: int | None = None,
    id_anexo: int | None = None,
    descartar_hasta: datetime | None = None,
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TableroProyeccionSchema:
    """Sin selección real, el de ejemplo. Restaura las decisiones del proceso
    salvo las anteriores a `descartar_hasta` ("Descartar y empezar limpio")."""
    if nro_proceso is None or id_grupo_economico is None or id_anexo is None:
        return await _tablero_ejemplo(fecha_objetivo, descartar_hasta)
    if fecha_objetivo is None:
        raise HTTPException(422, detail="fecha_objetivo es requerida para el tablero real")
    solicitud = SolicitudTableroSigesDto(
        nro_proceso, id_grupo_economico, id_anexo, fecha_objetivo, operador_de(identity)
    )
    resultado = await _tablero_real(db).execute(solicitud, descartar_hasta)
    return TableroProyeccionSchema.from_result(resultado)


async def _tablero_ejemplo(
    fecha_objetivo: date | None, descartar_hasta: datetime | None
) -> TableroProyeccionSchema:
    ctx = await contexto_ejemplo(fecha_objetivo)
    restauracion = SolicitudRestauracionDto(NRO_PROCESO_EJEMPLO, descartar_hasta)
    use_case = GetTableroProyeccionUseCase(get_decisiones_operador_store())
    return TableroProyeccionSchema.from_result(await use_case.execute(ctx, restauracion))


def _tablero_real(db: AsyncSession) -> GetTableroProyeccionSigesUseCase:
    """Con los candidatos de Siges para releer una P/L manual por
    `ID_Contador` al restaurarla, como el legacy."""
    return GetTableroProyeccionSigesUseCase(
        get_grilla_estimacion_gateway(),
        SqlAlchemyDecisionesOperadorRepository(db),
        SqlAlchemyRecesosRepository(db),
        get_candidatos_equipo_gateway(),
    )


@router.get("/export")
async def exportar_csv(
    nro_proceso: int,
    id_grupo_economico: int,
    id_anexo: int,
    fecha_objetivo: date,
    solo_estimados: bool = False,
    descartar_hasta: datetime | None = None,
    identity: Identity = _require_operar,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Response:
    """Export a SiGes (`CsvExportService` v1.7) de los equipos efectivos del
    tablero — solo proceso real. `solo_estimados`: opción "Solo estimados"
    del menú (sin reales ni pendientes). Windows-1252 sin BOM, separador ";",
    una fila por máquina."""
    solicitud = SolicitudTableroSigesDto(
        nro_proceso, id_grupo_economico, id_anexo, fecha_objetivo, operador_de(identity)
    )
    opciones = OpcionesExportCsv(solo_estimados, descartar_hasta)
    contenido = await _export(db).execute(solicitud, opciones)
    return _response_csv(contenido, _nombre_csv(nro_proceso, fecha_objetivo, solo_estimados))


def _export(db: AsyncSession) -> GenerarExportCsvUseCase:
    return GenerarExportCsvUseCase(
        get_grilla_estimacion_gateway(),
        SqlAlchemyDecisionesOperadorRepository(db),
        SqlAlchemyRecesosRepository(db),
        SqlAlchemyEstimLogRepository(db),
        get_candidatos_equipo_gateway(),
    )


def _nombre_csv(nro_proceso: int, fecha_objetivo: date, solo_estimados: bool) -> str:
    """`Estimacion_{NroProceso}_{yyyyMMdd}[_estimados].csv`, como el legacy."""
    sufijo = "_estimados" if solo_estimados else ""
    return f"Estimacion_{nro_proceso}_{fecha_objetivo:%Y%m%d}{sufijo}.csv"


def _response_csv(contenido: str, nombre: str) -> Response:
    """Windows-1252 sin BOM, con el mismo "best fit" de .NET que el legacy."""
    return Response(
        content=codificar_cp1252(contenido),
        media_type="text/csv; charset=windows-1252",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


router.include_router(candidatos_router)
router.include_router(recesos_router)
router.include_router(historial_router)
