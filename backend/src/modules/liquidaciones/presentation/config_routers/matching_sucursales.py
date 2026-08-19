"""Endpoints de matching de sucursales Tabla KM ↔ Siges (Fase 1): auto-vínculo
N1 en bloque, propuestas N2 (siempre requieren confirmación humana), y las
acciones de confirmar/rechazar un candidato."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.presentation.config_routers._deps import (
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.dependencies.matching_sucursales import (
    build_auto_vincular_n1,
    build_confirmar_vinculo,
    build_listar_propuestas_n2,
    build_rechazar_propuesta,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import TablaKmOut
from src.modules.liquidaciones.presentation.schemas.matching_sucursales_schemas import (
    ConfirmarVinculoIn,
    PropuestaN2Out,
    RechazarPropuestaIn,
    ResultadoAutoVinculoN1Out,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter()


@router.post(
    "/siges/prestador/{prestador_id}/matching/auto-vincular-n1",
    response_model=ResultadoAutoVinculoN1Out,
)
async def auto_vincular_n1(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> ResultadoAutoVinculoN1Out:
    """Vincula en bloque las filas con match exacto bajo normalización fuerte
    (símbolo/abreviatura) — aprobado como auto-vínculo (decisión 0.4.a).
    Idempotente: re-ejecutarlo sobre filas ya vinculadas no hace nada."""
    resultado = await build_auto_vincular_n1(db).execute(prestador_id)
    return ResultadoAutoVinculoN1Out.from_dto(resultado)


@router.get(
    "/siges/prestador/{prestador_id}/matching/propuestas",
    response_model=list[PropuestaN2Out],
)
async def listar_propuestas_n2(
    prestador_id: UUID,
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> list[PropuestaN2Out]:
    """Candidatos difusos (N2) pendientes de confirmación humana — nunca se
    auto-vinculan. Excluye los ya descartados por un operador."""
    propuestas = await build_listar_propuestas_n2(db).execute(prestador_id)
    return [PropuestaN2Out.from_dto(p) for p in propuestas]


@router.post("/tabla-km/{tabla_km_id}/matching/confirmar", response_model=TablaKmOut)
async def confirmar_vinculo(
    tabla_km_id: UUID,
    body: ConfirmarVinculoIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> TablaKmOut:
    fila = await build_confirmar_vinculo(db).execute(tabla_km_id, body.siges_sucursal_id)
    return TablaKmOut.from_entity(fila)


@router.post("/tabla-km/{tabla_km_id}/matching/rechazar", status_code=204)
async def rechazar_propuesta(
    tabla_km_id: UUID,
    body: RechazarPropuestaIn,
    identity: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    await build_rechazar_propuesta(db).execute(
        tabla_km_id, body.siges_sucursal_id, identity.user.email
    )
