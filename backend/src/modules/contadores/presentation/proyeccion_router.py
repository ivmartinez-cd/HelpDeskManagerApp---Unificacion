"""Herramienta Proyección — reactivada primero con datos de ejemplo (ver
`infrastructure/ejemplo/datos_ejemplo_proyeccion.py`), ya conectada a Siges
real para combos, grilla y candidatos (`SiGesReadOnly`). Sin selección real
de grupo/proceso, `/tablero` sigue devolviendo el tablero de ejemplo — ver
docstring de `get_tablero` más abajo. Los endpoints de candidatos viven en
`proyeccion_candidatos_router.py` (mismo prefix, incluido al final de este
archivo) para no pasar el máximo de 300 líneas."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases.gestionar_recesos_proyeccion import (
    CrearRecesoRequest,
    GestionarRecesosProyeccionUseCase,
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
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    ID_GRUPO_ECONOMICO_EJEMPLO,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    get_decisiones_operador_store,
)
from src.modules.contadores.infrastructure.ejemplo.recesos_store import get_recesos_ejemplo_store
from src.modules.contadores.presentation._proyeccion_contexto_ejemplo import contexto_ejemplo
from src.modules.contadores.presentation.dependencies import (
    get_grilla_estimacion_gateway,
    get_proceso_estimacion_gateway,
)
from src.modules.contadores.presentation.proyeccion_candidatos_router import (
    router as candidatos_router,
)
from src.modules.contadores.presentation.schemas.proyeccion_schemas import (
    AnexoOptionSchema,
    GrupoEconomicoOptionSchema,
    ProcesoOptionSchema,
    RecesoSchema,
    TableroProyeccionSchema,
)
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores/proyeccion", tags=["contadores-proyeccion"])

_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))
_TAMANIO_PAGINA_CATALOGO_CHICO = 50


@router.get("/grupos-economicos", response_model=Page[GrupoEconomicoOptionSchema])
async def list_grupos_economicos(
    _: Identity = _require_view,
) -> Page[GrupoEconomicoOptionSchema]:
    """Combo real contra Siges (MODELO_DE_DATOS.md §3.1) — el resto del
    tablero (`/tablero`) todavía usa datos de ejemplo, ver docstring del
    módulo."""
    grupos = await ListGruposEconomicosEstimacionUseCase(get_proceso_estimacion_gateway()).execute()
    items = [GrupoEconomicoOptionSchema.model_validate(g) for g in grupos]
    return Page.of(items, page=1, size=_TAMANIO_PAGINA_CATALOGO_CHICO)


@router.get("/procesos", response_model=Page[ProcesoOptionSchema])
async def list_procesos(
    id_grupo_economico: int, _: Identity = _require_view
) -> Page[ProcesoOptionSchema]:
    """Combo real contra Siges (MODELO_DE_DATOS.md §3.2), en cascada tras
    elegir un grupo económico."""
    use_case = ListProcesosPorGrupoEstimacionUseCase(get_proceso_estimacion_gateway())
    procesos = await use_case.execute(id_grupo_economico)
    items = [ProcesoOptionSchema.model_validate(p) for p in procesos]
    return Page.of(items, page=1, size=_TAMANIO_PAGINA_CATALOGO_CHICO)


@router.get("/anexos", response_model=Page[AnexoOptionSchema])
async def list_anexos(
    id_grupo_economico: int, _: Identity = _require_view
) -> Page[AnexoOptionSchema]:
    """Combo real contra Siges (MODELO_DE_DATOS.md §3.3) — acota el alcance
    de un receso a un anexo puntual en vez de todo el grupo."""
    use_case = ListAnexosPorGrupoEstimacionUseCase(get_proceso_estimacion_gateway())
    anexos = await use_case.execute(id_grupo_economico)
    items = [AnexoOptionSchema.model_validate(a) for a in anexos]
    return Page.of(items, page=1, size=_TAMANIO_PAGINA_CATALOGO_CHICO)


@router.get("/tablero", response_model=TableroProyeccionSchema)
async def get_tablero(
    fecha_objetivo: date | None = None,
    nro_proceso: int | None = None,
    id_grupo_economico: int | None = None,
    id_anexo: int | None = None,
    _: Identity = _require_view,
) -> TableroProyeccionSchema:
    """Sin `nro_proceso` (ni el resto de la selección real) sigue devolviendo
    el tablero de ejemplo — el día que el frontend siempre mande la
    selección real, este fallback se puede sacar."""
    if nro_proceso is None or id_grupo_economico is None or id_anexo is None:
        store = get_decisiones_operador_store()
        resultado = GetTableroProyeccionUseCase(store).execute(contexto_ejemplo(fecha_objetivo))
        return TableroProyeccionSchema.from_result(resultado)
    if fecha_objetivo is None:
        raise HTTPException(422, detail="fecha_objetivo es requerida para el tablero real")
    solicitud = SolicitudTableroSigesDto(nro_proceso, id_grupo_economico, id_anexo, fecha_objetivo)
    return await _get_tablero_real(solicitud)


async def _get_tablero_real(solicitud: SolicitudTableroSigesDto) -> TableroProyeccionSchema:
    use_case = GetTableroProyeccionSigesUseCase(
        get_grilla_estimacion_gateway(),
        get_decisiones_operador_store(),
        get_recesos_ejemplo_store(),
    )
    resultado = await use_case.execute(solicitud)
    return TableroProyeccionSchema.from_result(resultado)


@router.get("/recesos", response_model=Page[RecesoSchema])
async def list_recesos(_: Identity = _require_view) -> Page[RecesoSchema]:
    recesos = get_recesos_ejemplo_store().listar(ID_GRUPO_ECONOMICO_EJEMPLO)
    items = [RecesoSchema.from_dto(r) for r in recesos]
    return Page.of(items, page=1, size=_TAMANIO_PAGINA_CATALOGO_CHICO)


@router.post("/recesos", response_model=RecesoSchema)
async def crear_receso(
    request: CrearRecesoRequest, _: Identity = _require_manage
) -> RecesoSchema:
    use_case = GestionarRecesosProyeccionUseCase(get_recesos_ejemplo_store())
    return RecesoSchema.from_dto(use_case.crear(request))


@router.delete("/recesos/{id_receso}", status_code=204)
async def eliminar_receso(id_receso: int, _: Identity = _require_manage) -> None:
    GestionarRecesosProyeccionUseCase(get_recesos_ejemplo_store()).eliminar(id_receso)


router.include_router(candidatos_router)
