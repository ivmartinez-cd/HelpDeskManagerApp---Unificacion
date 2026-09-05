"""Panel de candidatos del Estimador — extraído de `proyeccion_router.py` para
respetar el máximo de 300 líneas por archivo (ARCHITECTURE_GUIDE.md §4);
se incluye en ese router (mismo prefix, ver `router.include_router` al final
de ese archivo)."""

from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.forzar_metodo_request import ForzarMetodoRequest
from src.modules.contadores.application.dtos.recalcular_candidato_request import (
    RecalcularCandidatoRequest,
)
from src.modules.contadores.application.use_cases.forzar_metodo_candidato import (
    ForzarMetodoCandidatoUseCase,
)
from src.modules.contadores.application.use_cases.forzar_metodo_candidato_siges import (
    ForzarMetodoCandidatoSigesUseCase,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo import (
    GetCandidatosEquipoUseCase,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo_siges import (
    GetCandidatosEquipoSigesUseCase,
)
from src.modules.contadores.application.use_cases.recalcular_candidato import (
    RecalcularCandidatoUseCase,
)
from src.modules.contadores.application.use_cases.recalcular_candidato_siges import (
    RecalcularCandidatoSigesUseCase,
)
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    get_decisiones_operador_store,
)
from src.modules.contadores.infrastructure.ejemplo.recesos_store import get_recesos_ejemplo_store
from src.modules.contadores.presentation._proyeccion_auditoria import (
    registrar_accion,
    registrar_metodo_forzado,
    registrar_pl_manual,
)
from src.modules.contadores.presentation._proyeccion_contexto_ejemplo import contexto_ejemplo
from src.modules.contadores.presentation._proyeccion_solicitud_real import (
    es_solicitud_real,
    solicitud_de,
)
from src.modules.contadores.presentation.dependencies import (
    get_candidatos_equipo_gateway,
    get_grilla_estimacion_gateway,
)
from src.modules.contadores.presentation.schemas.proyeccion_schemas import (
    CandidatosEquipoSchema,
    RecalcularCandidatoResponseSchema,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter()

_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


@router.get("/candidatos/{id_maquina}/{clase}", response_model=CandidatosEquipoSchema)
async def get_candidatos(
    id_maquina: int,
    clase: str,
    fecha_objetivo: date | None = None,
    _: Identity = _require_view,
) -> CandidatosEquipoSchema:
    """`clase` de un equipo de ejemplo es un código (`"A4-B/N"`); `clase` de
    un equipo real de Siges es el `ID_ClaseContador` como string (ver
    `_clase_de` en `_mapear_filas_grilla_siges.py`) — de ahí el fallback."""
    dto = GetCandidatosEquipoUseCase().execute(id_maquina, clase, contexto_ejemplo(fecha_objetivo))
    if dto is None and clase.isdigit():
        use_case = GetCandidatosEquipoSigesUseCase(get_candidatos_equipo_gateway())
        dto = await use_case.execute(id_maquina, int(clase))
    if dto is None:
        raise HTTPException(status_code=404, detail="Equipo o clase no encontrado")
    return CandidatosEquipoSchema.from_dto(dto)


@router.post("/candidatos/recalcular", response_model=RecalcularCandidatoResponseSchema)
async def recalcular_candidato(
    request: RecalcularCandidatoRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> RecalcularCandidatoResponseSchema:
    resultado = RecalcularCandidatoUseCase().execute(request, contexto_ejemplo(None))
    if resultado is None and es_solicitud_real(request):
        use_case = RecalcularCandidatoSigesUseCase(
            get_grilla_estimacion_gateway(), get_recesos_ejemplo_store()
        )
        resultado = await use_case.execute(request, solicitud_de(request))
    if resultado is None:
        raise HTTPException(
            status_code=422, detail="Pareja Partida/Llegada inválida (separación < 15 días o L < P)"
        )
    await registrar_pl_manual(db, identity, request, resultado)
    return RecalcularCandidatoResponseSchema.from_resultado(resultado)


@router.post("/candidatos/forzar", response_model=RecalcularCandidatoResponseSchema)
async def forzar_metodo_candidato(
    request: ForzarMetodoRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> RecalcularCandidatoResponseSchema:
    """Dos de las 5 acciones manuales de REGLAS_DE_NEGOCIO §8 ("forzar
    cascada de parque" / "forzar entre dos reales") — mismo criterio de
    fallback ejemplo→real que `recalcular_candidato`."""
    resultado = ForzarMetodoCandidatoUseCase().execute(request, contexto_ejemplo(None))
    if resultado is None and es_solicitud_real(request):
        use_case = ForzarMetodoCandidatoSigesUseCase(
            get_grilla_estimacion_gateway(), get_recesos_ejemplo_store()
        )
        resultado = await use_case.execute(request, solicitud_de(request))
    if resultado is None:
        raise HTTPException(
            status_code=422,
            detail="No se pudo forzar ese método: no hay datos suficientes (par válido o parque)",
        )
    await registrar_metodo_forzado(db, identity, request, resultado)
    return RecalcularCandidatoResponseSchema.from_resultado(resultado)


@router.post("/candidatos/{id_maquina}/{clase}/marcar-pendiente", status_code=204)
async def marcar_pendiente(
    id_maquina: int,
    clase: str,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    get_decisiones_operador_store().marcar_pendiente(id_maquina, clase)
    await registrar_accion(db, identity, id_maquina, clase, "marcar_pendiente")


@router.post("/candidatos/{id_maquina}/{clase}/nota", status_code=204)
async def agregar_nota(
    id_maquina: int,
    clase: str,
    nota: str = Body(embed=True),
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    get_decisiones_operador_store().agregar_nota(id_maquina, clase, nota)
    await registrar_accion(db, identity, id_maquina, clase, "agregar_nota", observacion=nota)


@router.post("/candidatos/{id_maquina}/{clase}/aceptar", status_code=204)
async def aceptar_propuesta(
    id_maquina: int,
    clase: str,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    get_decisiones_operador_store().aceptar(id_maquina, clase)
    await registrar_accion(db, identity, id_maquina, clase, "aceptar_sugerencia")
