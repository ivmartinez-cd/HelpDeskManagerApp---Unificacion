"""Gestión de alertas ALT por liquidación — la TL revisa/resuelve/descarta.

Router propio (liquidaciones_router.py está al límite §4). A diferencia del
PATCH de observaciones (repo directo), este pasa por `ActualizarEstadoAlerta`
porque además recalcula `estado_validacion` del incidente dueño — no es un
simple update de un solo campo. 404 si la alerta no pertenece a la
liquidación. La justificación obligatoria al descartar la valida el schema."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.well_known_permissions import UPDATE
from src.modules.liquidaciones.presentation.dependencies.liquidaciones import (
    build_actualizar_estado_alerta,
)
from src.modules.liquidaciones.presentation.schemas.liquidacion_detalle_schemas import (
    AlertaEstadoIn,
    AlertaOut,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])

_require_update = Depends(require_permission(UPDATE))


@router.patch("/{liquidacion_id}/alertas/{alerta_id}/estado", response_model=AlertaOut)
async def update_estado_alerta(
    liquidacion_id: UUID,
    alerta_id: UUID,
    body: AlertaEstadoIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AlertaOut:
    updated = await build_actualizar_estado_alerta(db).execute(
        liquidacion_id,
        alerta_id,
        estado=body.estado,
        justificacion=body.justificacion,
        incidente_relacionado_id=body.incidente_relacionado_id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return AlertaOut.from_entity(updated)
