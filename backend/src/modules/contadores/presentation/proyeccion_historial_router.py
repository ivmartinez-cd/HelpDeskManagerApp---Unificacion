"""Línea de tiempo de un equipo (MODELO_DE_DATOS.md §3.6, paridad con
`DrillDownModal` legacy) — extraído para no sumar a `proyeccion_router.py`,
que ya está cerca del máximo de 300 líneas (ARCHITECTURE_GUIDE.md §4);
incluido con el mismo prefix, ver `router.include_router` en ese archivo."""

from fastapi import APIRouter, Depends

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.use_cases.get_candidatos_equipo import (
    buscar_equipo_y_clase,
)
from src.modules.contadores.application.use_cases.get_historial_equipo import (
    GetHistorialEquipoUseCase,
)
from src.modules.contadores.domain.well_known_permissions import VIEW
from src.modules.contadores.presentation.dependencies import get_historial_equipo_gateway
from src.modules.contadores.presentation.schemas.proyeccion_schemas import HistorialEquipoSchema

router = APIRouter()

_require_view = Depends(require_permission(VIEW))


@router.get("/equipos/{id_maquina}/{clase}/historial", response_model=HistorialEquipoSchema)
async def get_historial_equipo(
    id_maquina: int,
    clase: str,
    _: Identity = _require_view,
) -> HistorialEquipoSchema:
    """Un equipo de ejemplo (`clase` no numérica) no tiene historial real de
    Siges: se devuelve vacío en vez de 404 para que el modal solo muestre
    "Sin lecturas registradas", igual criterio que 0 resultados reales."""
    equipo, _ = buscar_equipo_y_clase(id_maquina, clase)
    if equipo is not None or not clase.isdigit():
        return HistorialEquipoSchema(lecturas=[])
    use_case = GetHistorialEquipoUseCase(get_historial_equipo_gateway())
    lecturas = await use_case.execute(id_maquina, int(clase))
    return HistorialEquipoSchema.from_lecturas(lecturas)
