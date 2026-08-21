"""Endpoints del pipeline de geovalidación (Tier 0 → Tier 1 → Tier 1b →
worklist Tier 2), separado de `geolocalizacion.py` porque ese archivo ya
superaba el tamaño máximo (§4). Mismo prefijo `/api/liquidaciones` (montado
por `config_router.py`)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.presentation import _liq_csv_export as csv_export
from src.modules.liquidaciones.presentation.config_routers._deps import (
    require_export,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_calcular_worklist_tier2,
    build_consultar_georef_pendientes,
    build_consultar_nominatim_pendientes,
    build_evaluar_tier0,
    build_generar_worklist_csv,
    build_listar_hallazgos_tier1,
    build_listar_hallazgos_tier1b,
)
from src.modules.liquidaciones.presentation.schemas.geovalidacion_tier0_schemas import (
    HallazgoTier0Out,
)
from src.modules.liquidaciones.presentation.schemas.geovalidacion_tier1_schemas import (
    HallazgoTier1Out,
    ResultadoConsultarGeorefOut,
)
from src.modules.liquidaciones.presentation.schemas.geovalidacion_tier1b_schemas import (
    HallazgoTier1bOut,
    ResultadoConsultarNominatimOut,
)
from src.modules.liquidaciones.presentation.schemas.geovalidacion_worklist_schemas import (
    ResultadoWorklistTier2Out,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get(
    "/siges/prestador/{prestador_id}/geovalidacion/tier0",
    response_model=Page[HallazgoTier0Out],
)
async def geovalidacion_tier0(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[HallazgoTier0Out]:
    """Worklist de saneo geométrico (Tier 0): coordenadas ausentes/inválidas,
    fuera de Argentina, lat/lon invertidas, pin compartido entre sucursales
    con domicilio distinto y distancia a la base — rankeada por severidad,
    sin costo (cero llamadas a Georef/Nominatim/Google)."""
    hallazgos = await build_evaluar_tier0(db).execute(prestador_id)
    return Page.of([HallazgoTier0Out.from_dto(h) for h in hallazgos], page=page, size=size)


@router.post(
    "/siges/prestador/{prestador_id}/geovalidacion/tier1/consultar-georef",
    response_model=ResultadoConsultarGeorefOut,
)
async def consultar_georef(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ResultadoConsultarGeorefOut:
    """Reverse geocoding de Georef (gratis, sin auth) para sucursales con pin
    todavía sin cachear — secuencial, con pausa y tope por corrida. Repetir
    esta acción no vuelve a consultar lo ya cacheado."""
    resultado = await build_consultar_georef_pendientes(db).execute(prestador_id)
    return ResultadoConsultarGeorefOut.from_dto(resultado)


@router.get(
    "/siges/prestador/{prestador_id}/geovalidacion/tier1",
    response_model=Page[HallazgoTier1Out],
)
async def geovalidacion_tier1(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[HallazgoTier1Out]:
    """Sucursales donde la provincia declarada en Siges no coincide con la
    que devolvió el reverse de Georef para el pin — solo sobre lo ya
    consultado (`consultar-georef`), no llama a nada."""
    hallazgos = await build_listar_hallazgos_tier1(db).execute(prestador_id)
    return Page.of([HallazgoTier1Out.from_dto(h) for h in hallazgos], page=page, size=size)


@router.post(
    "/siges/prestador/{prestador_id}/geovalidacion/tier1b/consultar-nominatim",
    response_model=ResultadoConsultarNominatimOut,
)
async def consultar_nominatim(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ResultadoConsultarNominatimOut:
    """Segunda opinión de Nominatim (OpenStreetMap, gratis), SOLO sobre lo
    que Georef ya marcó con provincia incompatible — rate limit de 1 req/s
    aplicado por el adapter. Datos © OpenStreetMap contributors, ODbL 1.0."""
    resultado = await build_consultar_nominatim_pendientes(db).execute(prestador_id)
    return ResultadoConsultarNominatimOut.from_dto(resultado)


@router.get(
    "/siges/prestador/{prestador_id}/geovalidacion/tier1b",
    response_model=Page[HallazgoTier1bOut],
)
async def geovalidacion_tier1b(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[HallazgoTier1bOut]:
    """Hallazgos confirmados por DOS fuentes independientes (Georef +
    Nominatim de acuerdo) — solo sobre lo ya consultado, no llama a nada."""
    hallazgos = await build_listar_hallazgos_tier1b(db).execute(prestador_id)
    return Page.of([HallazgoTier1bOut.from_dto(h) for h in hallazgos], page=page, size=size)


@router.get(
    "/siges/prestador/{prestador_id}/geovalidacion/worklist",
    response_model=ResultadoWorklistTier2Out,
)
async def geovalidacion_worklist(
    prestador_id: UUID,
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ResultadoWorklistTier2Out:
    """Residuo real tras Tier 0+1+1b — separa lo que ya tiene certeza
    absoluta (corregir directo, sin Google) de lo que genuinamente
    ameritaría Tier 2, con la estimación de llamadas nuevas a Google
    (`estimacionLlamadasGoogle`). No llama a Google, solo estima."""
    resultado = await build_calcular_worklist_tier2(db).execute(prestador_id)
    return ResultadoWorklistTier2Out.from_dto(resultado)


@router.get("/siges/prestador/{prestador_id}/geovalidacion/worklist/export")
async def geovalidacion_worklist_export(
    prestador_id: UUID,
    _: Identity = require_export,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> StreamingResponse:
    """CSV para Gestión (Siges es read-only): junta Tier 0 certeza absoluta +
    Tier 1b confirmado por dos fuentes + Tier 2 confirmado por Google en un
    solo listado con Id_Sucursal, pin actual y pin sugerido."""
    prestador = await SqlAlchemyPrestadorRepository(db).get_by_id(prestador_id)
    clave = prestador.nombre_corto if prestador else str(prestador_id)
    filas = await build_generar_worklist_csv(db).execute(prestador_id)
    return csv_export.export_worklist_geovalidacion(filas, clave)
