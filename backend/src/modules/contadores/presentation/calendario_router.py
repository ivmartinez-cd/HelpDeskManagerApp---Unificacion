"""Router del calendario de contadores — agrega los sub-routers por responsabilidad.

Todos comparten el prefijo /api/contadores; las rutas y contratos no cambian
respecto del router monolítico original (mismo criterio que el config_router
de liquidaciones)."""

from fastapi import APIRouter

from src.modules.contadores.presentation.calendario_routers import (
    clientes_siges,
    eventos,
    overrides,
    sync,
)

router = APIRouter(prefix="/api/contadores", tags=["contadores-calendario"])
router.include_router(eventos.router)
router.include_router(sync.router)
router.include_router(clientes_siges.router)
router.include_router(overrides.router)
