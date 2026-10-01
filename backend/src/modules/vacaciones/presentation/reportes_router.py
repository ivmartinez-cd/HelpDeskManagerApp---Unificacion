from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.features import require_feature
from src.modules.vacaciones.application.dtos.reporte_dtos import ReporteVacacionesDTO
from src.modules.vacaciones.application.use_cases.reporte_vacaciones import (
    ReporteVacaciones,
    ReporteVacacionesDependencies,
)
from src.modules.vacaciones.domain.well_known_features import REPORTES
from src.modules.vacaciones.infrastructure.exports.reporte_vacaciones_archivos import (
    reporte_excel,
    reporte_pdf,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_cargo_repository import (
    SqlAlchemyCargoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ciclo_repository import (
    SqlAlchemyCicloRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_config_repository import (
    SqlAlchemyConfigRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_repository import (
    SqlAlchemySectorRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_solicitud_repository import (  # noqa: E501
    SqlAlchemySolicitudRepository,
)
from src.modules.vacaciones.infrastructure.system_clock import SystemClock
from src.modules.vacaciones.presentation.schemas.reporte_schemas import (
    ReporteVacacionesResponse,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/vacaciones/reportes", tags=["vacaciones"])
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _adjunto(contenido: bytes, media_type: str, filename: str) -> Response:
    disposicion = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(contenido, media_type=media_type, headers=disposicion)

# Función concedible por usuario (ADR-032): antes vacaciones.manage.
_require_manage = Depends(require_feature(REPORTES))


async def _generar(db: AsyncSession) -> ReporteVacacionesDTO:
    deps = ReporteVacacionesDependencies(
        empleados=SqlAlchemyEmpleadoRepository(db),
        sectores=SqlAlchemySectorRepository(db),
        cargos=SqlAlchemyCargoRepository(db),
        ciclos=SqlAlchemyCicloRepository(db),
        solicitudes=SqlAlchemySolicitudRepository(db),
        config=SqlAlchemyConfigRepository(db),
        clock=SystemClock(),
    )
    return await ReporteVacaciones(deps).execute()


@router.get("")
async def get_reporte(
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ReporteVacacionesResponse:
    return ReporteVacacionesResponse.from_dto(await _generar(db))


@router.get("/excel")
async def get_reporte_excel(
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Response:
    return _adjunto(reporte_excel(await _generar(db)), _XLSX, "reporte-vacaciones.xlsx")


@router.get("/pdf")
async def get_reporte_pdf(
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Response:
    contenido = reporte_pdf(await _generar(db), timezone=get_settings().app_timezone)
    return _adjunto(contenido, "application/pdf", "reporte-vacaciones.pdf")
