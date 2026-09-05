"""Router de configuración de liquidaciones — agrega los sub-routers por entidad.

Todos comparten el prefijo /api/liquidaciones. Dentro de cada sub-router, las rutas
con segmento literal (export, import) van antes de las que usan {id} para evitar que
FastAPI intente parsear "export" como UUID."""

from fastapi import APIRouter

from src.modules.liquidaciones.presentation.config_routers import (
    acuerdos,
    geolocalizacion,
    geovalidacion,
    matching_sucursales,
    prestadores,
    reglas,
    siges,
    spsts,
    tabla_km,
    tabla_km_geo,
    tarifarios,
)

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones-config"])
router.include_router(prestadores.router)
router.include_router(spsts.router)
router.include_router(tarifarios.router)
router.include_router(tabla_km.router)
router.include_router(siges.router)
router.include_router(geolocalizacion.router)
router.include_router(geovalidacion.router)
router.include_router(tabla_km_geo.router)
router.include_router(matching_sucursales.router)
router.include_router(reglas.router)
router.include_router(acuerdos.router)
