"""Panel de candidatos del Estimador — extraído de `proyeccion_router.py` para
respetar el máximo de 300 líneas por archivo (ARCHITECTURE_GUIDE.md §4);
se incluye en ese router (mismo prefix, ver `router.include_router` al final
de ese archivo)."""

from datetime import date
from typing import cast

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.decision_operador_dto import DecisionManualDto
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
    buscar_equipo_y_clase,
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
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    get_decisiones_operador_store,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_decisiones_operador_repository import (  # noqa: E501
    SqlAlchemyDecisionesOperadorRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_recesos_repository import (
    SqlAlchemyRecesosRepository,
)
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


class AceptarManualBody(BaseModel):
    """El último cálculo que el operador vio (P/L manual o método forzado) y
    decidió confirmar — si viene vacío, "aceptar" confirma el automático."""

    contador_propuesto: float | None = None
    tipo_toma: int | None = None
    fuente: str | None = None
    metodo_detalle: str | None = None


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
    dto = GetCandidatosEquipoUseCase().execute(
        id_maquina, clase, await contexto_ejemplo(fecha_objetivo)
    )
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
    resultado = RecalcularCandidatoUseCase().execute(request, await contexto_ejemplo(None))
    if resultado is None and es_solicitud_real(request):
        use_case = RecalcularCandidatoSigesUseCase(
            get_grilla_estimacion_gateway(), SqlAlchemyRecesosRepository(db)
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
    """Forzar cascada de parque / entre reales (REGLAS_DE_NEGOCIO §8)."""
    resultado = ForzarMetodoCandidatoUseCase().execute(request, await contexto_ejemplo(None))
    if resultado is None and es_solicitud_real(request):
        use_case = ForzarMetodoCandidatoSigesUseCase(
            get_grilla_estimacion_gateway(), SqlAlchemyRecesosRepository(db)
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
    await _decisiones_store_de(id_maquina, clase, db).marcar_pendiente(id_maquina, clase)
    await registrar_accion(db, identity, id_maquina, clase, "marcar_pendiente")


@router.post("/candidatos/{id_maquina}/{clase}/nota", status_code=204)
async def agregar_nota(
    id_maquina: int,
    clase: str,
    nota: str = Body(embed=True),
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await _decisiones_store_de(id_maquina, clase, db).agregar_nota(id_maquina, clase, nota)
    await registrar_accion(db, identity, id_maquina, clase, "agregar_nota", observacion=nota)


@router.post("/candidatos/{id_maquina}/{clase}/aceptar", status_code=204)
async def aceptar_propuesta(
    id_maquina: int,
    clase: str,
    body: AceptarManualBody | None = None,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    manual = _decision_manual_de(body)
    await _decisiones_store_de(id_maquina, clase, db).aceptar(id_maquina, clase, manual)
    campos = (
        {
            "contador_propuesto": manual.contador_propuesto,
            "tipo_toma_grabado": manual.tipo_toma,
            "fuente": manual.fuente,
            "metodo_detalle": manual.metodo_detalle,
        }
        if manual
        else {}
    )
    await registrar_accion(db, identity, id_maquina, clase, "aceptar_sugerencia", **campos)


def _decision_manual_de(body: AceptarManualBody | None) -> DecisionManualDto | None:
    if body is None or body.fuente is None:
        return None
    return DecisionManualDto(
        contador_propuesto=body.contador_propuesto,
        tipo_toma=body.tipo_toma,
        fuente=cast(FuenteEstimacion, body.fuente),
        metodo_detalle=body.metodo_detalle or "",
    )


def _decisiones_store_de(id_maquina: int, clase: str, db: AsyncSession) -> DecisionesOperadorPort:
    """Un equipo real de Siges nunca aparece en `equipos_ejemplo()` — a
    diferencia de `es_solicitud_real` (que solo mira si `clase` es numérica),
    acá hace falta esa verificación extra porque el equipo de ejemplo id=1
    también tiene clase "10" (numérica): sin este chequeo, sus decisiones se
    escribirían en Postgres en vez del store en memoria (bug real, visto
    2026-09-05)."""
    equipo, _ = buscar_equipo_y_clase(id_maquina, clase)
    if equipo is None and clase.isdigit():
        return SqlAlchemyDecisionesOperadorRepository(db)
    return get_decisiones_operador_store()
