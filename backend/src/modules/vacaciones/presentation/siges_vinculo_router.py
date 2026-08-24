import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.domain.well_known_permissions import MANAGE
from src.modules.vacaciones.presentation.dependencies.siges import (
    build_proponer_vinculos_siges,
    build_vincular_empleado_siges,
)
from src.modules.vacaciones.presentation.schemas.empleado_schemas import EmpleadoResponse
from src.modules.vacaciones.presentation.schemas.siges_vinculo_schemas import (
    PropuestasVinculoResponse,
    VincularSigesIn,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/vacaciones", tags=["vacaciones"])

_require_manage = Depends(require_permission(MANAGE))


@router.get("/siges/propuestas", response_model=PropuestasVinculoResponse)
async def get_propuestas_siges(
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PropuestasVinculoResponse:
    """Propuestas de vínculo Empleado↔técnico de Siges por matching de
    nombre — la confirmación de cada una es manual (ver PUT siges-vinculo)."""
    resultado = await build_proponer_vinculos_siges(db).execute()
    return PropuestasVinculoResponse.from_resultado(resultado)


@router.put("/empleados/{empleado_id}/siges-vinculo", response_model=EmpleadoResponse)
async def vincular_empleado_siges(
    empleado_id: uuid.UUID,
    body: VincularSigesIn,
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> EmpleadoResponse:
    """Confirma (o quita, con `sigesEmpresaId: null`) el vínculo de un
    empleado con su técnico de Siges."""
    empleado = await build_vincular_empleado_siges(db).execute(
        empleado_id, siges_empresa_id=body.siges_empresa_id
    )
    return EmpleadoResponse.from_entity(empleado)
