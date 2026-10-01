"""Panel de candidatos y acciones del operador sobre una fila del tablero de
Proyección — incluido en `proyeccion_router.py` (mismo prefix). Mismo flujo
que `PanelCandidatos` + `GrillaEstimacion` del legacy:

- `recalcular`: vista previa de una P/L manual (no guarda ni audita).
- `forzar`: "Usar T19 (cascada)" / "Usar entre reales", se aplica al toque.
- `aceptar`: con Partida y Llegada, "Aceptar P/L manual" (con la observación
  escrita); sin ellas, "Aceptar sugerencia" (solo si la fila tiene valor
  propuesto; la observación escrita se descarta, como en v1.7).
- `marcar-pendiente`: la fila queda en blanco, con la observación escrita.

"+ Agregar nota" del legacy solo muestra la caja de texto: no hay una acción
que guarde una observación suelta.

Todas operan sobre la fila efectiva que muestra la grilla
(`proyeccion_operador/fila_vigente.py`, incluido el corte `descartar_hasta` de
"Descartar y empezar limpio"). La lógica de cada acción (decisión del
proceso + auditoría) vive en `application/use_cases/proyeccion_operador/acciones.py`."""

from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.features import require_feature_or_permission
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.application.dtos.decision_operador_dto import ParPartidaLlegadaDto
from src.modules.contadores.application.dtos.forzar_metodo_request import ForzarMetodoRequest
from src.modules.contadores.application.use_cases.forzar_metodo_candidato import forzar_metodo
from src.modules.contadores.application.use_cases.get_candidatos_equipo import (
    GetCandidatosEquipoUseCase,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo_siges import (
    GetCandidatosEquipoSigesUseCase,
)
from src.modules.contadores.application.use_cases.proyeccion_operador import acciones
from src.modules.contadores.application.use_cases.proyeccion_operador.acciones import FilaAccion
from src.modules.contadores.application.use_cases.proyeccion_operador.contexto_ejemplo import (
    contexto_ejemplo,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.fila_vigente import (
    FilaVigente,
    fila_vigente,
    par_de_siges,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.solicitud_real import (
    solicitud_real_de,
)
from src.modules.contadores.application.use_cases.recalcular_candidato import recalcular_pl
from src.modules.contadores.domain.well_known_features import PROYECCION_OPERAR
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.repositories.sqlalchemy_recesos_repository import (
    SqlAlchemyRecesosRepository,
)
from src.modules.contadores.presentation.dependencies import (
    get_candidatos_equipo_gateway,
    get_grilla_estimacion_gateway,
)
from src.modules.contadores.presentation.proyeccion_dependencias import (
    dependencias_proyeccion,
    operador_de,
    operador_proyeccion,
)
from src.modules.contadores.presentation.schemas.proyeccion_candidatos_schemas import (
    CandidatosEquipoSchema,
    RecalcularCandidatoResponseSchema,
)
from src.modules.contadores.presentation.schemas.proyeccion_decisiones_schemas import (
    AccionDecisionBody,
    AceptarDecisionBody,
    RecalcularPLBody,
    SeleccionProcesoSchema,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter()

_require_view = Depends(require_permission(VIEW))
# Elegir P/L, forzar método, aceptar y marcar pendiente: alcanza con la
# función "Proyección: operar candidatos" sin necesitar `contadores.manage`
# completo (recesos siguen exigiendo manage, ver `proyeccion_router.py`).
_require_operar = Depends(require_feature_or_permission(PROYECCION_OPERAR, MANAGE))
_db = Depends(get_db, scope="function")


@router.get("/candidatos/{id_maquina}/{clase}", response_model=CandidatosEquipoSchema)
async def get_candidatos(
    id_maquina: int,
    clase: str,
    seleccion: SeleccionProcesoSchema = Depends(),
    identity: Identity = _require_view,
    db: AsyncSession = _db,
) -> CandidatosEquipoSchema:
    """Selección real opcional: sin ella un equipo real igual se muestra,
    solo sin el gráfico de parque (necesita la grilla ya cargada del proceso)."""
    operador = operador_de(identity)
    dto = await _resolver_dto_candidatos(id_maquina, clase, seleccion, db, operador)
    if dto is None:
        raise HTTPException(status_code=404, detail="Equipo o clase no encontrado")
    deps = dependencias_proyeccion(db)
    vigente = await fila_vigente(id_maquina, clase, seleccion, deps, operador)
    return CandidatosEquipoSchema.from_dto(
        _con_boxplot_vigente(dto, vigente), _metodos_disponibles(vigente)
    )


def _metodos_disponibles(vigente: FilaVigente | None) -> tuple[bool, bool]:
    """(cascada, entre reales): los botones "Usar …" que el legacy ofrece
    para la fila efectiva (`PuedeUsarCascada` / `PuedeUsarEntreReales`,
    respetando "Descartar y empezar limpio") — lo mismo que después acepta
    `/candidatos/forzar`."""
    if vigente is None:
        return False, False
    cascada = forzar_metodo("cascada_parque", vigente.entrada, vigente.resultado) is not None
    entre = forzar_metodo("entre_reales", vigente.entrada, vigente.resultado) is not None
    return cascada, entre


def _con_boxplot_vigente(
    dto: CandidatosEquipoDto, vigente: FilaVigente | None
) -> CandidatosEquipoDto:
    """El "este equipo" del boxplot es `Equipo.Impresiones` de la fila efectiva
    (con la decisión del operador), como `PanelCandidatos.razor`."""
    if dto.boxplot is None or vigente is None:
        return dto
    boxplot = replace(dto.boxplot, valor_equipo=vigente.resultado.impresiones)
    return replace(dto, boxplot=boxplot)


async def _resolver_dto_candidatos(
    id_maquina: int,
    clase: str,
    seleccion: SeleccionProcesoSchema,
    db: AsyncSession,
    operador: str,
) -> CandidatosEquipoDto | None:
    solicitud = solicitud_real_de(seleccion, clase, operador)
    if solicitud is None:
        ctx = await contexto_ejemplo(seleccion.fecha_objetivo)
        dto = GetCandidatosEquipoUseCase().execute(id_maquina, clase, ctx)
        if dto is not None or not clase.isdigit():
            return dto
    use_case = GetCandidatosEquipoSigesUseCase(
        get_candidatos_equipo_gateway(), get_grilla_estimacion_gateway(),
        SqlAlchemyRecesosRepository(db),
    )
    return await use_case.execute(id_maquina, int(clase), solicitud)


@router.post("/candidatos/recalcular", response_model=RecalcularCandidatoResponseSchema)
async def recalcular_candidato(
    body: RecalcularPLBody, identity: Identity = _require_operar, db: AsyncSession = _db
) -> RecalcularCandidatoResponseSchema:
    """Vista previa (`PanelCandidatos.RecomputarPreview`): no guarda ni audita.
    En el modo real la P/L se relee de Siges por `ID_Contador`."""
    deps = dependencias_proyeccion(db)
    par = await par_de_siges(body.par(), body, deps)
    acciones.validar_lecturas_usables(par)
    fila = FilaAccion(par.id_maquina, par.clase, body, operador_de(identity))
    entrada = await acciones.entrada_o_404(fila, deps)
    resultado = recalcular_pl(par, entrada)
    if resultado is None:
        raise HTTPException(status_code=422, detail=acciones.PL_INVALIDA)
    return RecalcularCandidatoResponseSchema.from_resultado(resultado)


@router.post("/candidatos/forzar", response_model=RecalcularCandidatoResponseSchema)
async def forzar_metodo_candidato(
    request: ForzarMetodoRequest, identity: Identity = _require_operar, db: AsyncSession = _db
) -> RecalcularCandidatoResponseSchema:
    """Se aplica al toque, como los botones "Usar …" del legacy. 422 si el
    legacy no ofrece ese botón para la fila (sin par válido, cascada sin
    datos, o la fila ya sale de ese método)."""
    deps = dependencias_proyeccion(db)
    resultado = await acciones.forzar(request, operador_proyeccion(identity), deps)
    return RecalcularCandidatoResponseSchema.from_resultado(resultado)


@router.post("/candidatos/{id_maquina}/{clase}/marcar-pendiente", status_code=204)
async def marcar_pendiente(
    id_maquina: int,
    clase: str,
    body: AccionDecisionBody | None = None,
    identity: Identity = _require_operar,
    db: AsyncSession = _db,
) -> None:
    """Graba la observación escrita junto con la acción (`HandleMarcarPendiente`)."""
    body = body or AccionDecisionBody()
    fila = FilaAccion(id_maquina, clase, body, operador_de(identity))
    operador = operador_proyeccion(identity)
    await acciones.marcar_pendiente(fila, body.nota_limpia(), operador, dependencias_proyeccion(db))


@router.post("/candidatos/{id_maquina}/{clase}/aceptar", status_code=204)
async def aceptar(
    id_maquina: int,
    clase: str,
    body: AceptarDecisionBody | None = None,
    identity: Identity = _require_operar,
    db: AsyncSession = _db,
) -> None:
    """Con Partida y Llegada, "Aceptar P/L manual"; sin ninguna de las dos,
    "Aceptar sugerencia" (ignora `nota`, ver `aceptar_sugerencia`)."""
    body = body or AceptarDecisionBody()
    fila = FilaAccion(id_maquina, clase, body, operador_de(identity))
    operador, deps = operador_proyeccion(identity), dependencias_proyeccion(db)
    if body.partida is None and body.llegada is None:
        await acciones.aceptar_sugerencia(fila, operador, deps)
        return
    if body.partida is None or body.llegada is None:
        raise HTTPException(status_code=422, detail="Falta la Partida o la Llegada")
    par = ParPartidaLlegadaDto(id_maquina, clase, body.partida.a_dto(), body.llegada.a_dto())
    await acciones.aceptar_pl(fila, par, body.nota_limpia(), operador, deps)
