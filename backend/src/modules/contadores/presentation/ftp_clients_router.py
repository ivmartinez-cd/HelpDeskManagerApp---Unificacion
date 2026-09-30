import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.download_ftp_db3_request import DownloadFtpDb3Request
from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientRequest
from src.modules.contadores.application.use_cases.create_ftp_client import CreateFtpClientUseCase
from src.modules.contadores.application.use_cases.delete_ftp_client import DeleteFtpClientUseCase
from src.modules.contadores.application.use_cases.download_and_process_ftp_db3 import (
    DownloadAndProcessFtpDb3UseCase,
)
from src.modules.contadores.application.use_cases.get_ftp_client import GetFtpClientUseCase
from src.modules.contadores.application.use_cases.list_ftp_clients import ListFtpClientsUseCase
from src.modules.contadores.application.use_cases.run_db3_export import RunDb3ExportUseCase
from src.modules.contadores.application.use_cases.update_ftp_client import UpdateFtpClientUseCase
from src.modules.contadores.domain.repositories.grupos_economicos_ftp_gateway import (
    GruposEconomicosFtpGateway,
)
from src.modules.contadores.domain.well_known_permissions import EXPORT
from src.modules.contadores.infrastructure.csv.csv_db3_writer import CsvDb3Writer
from src.modules.contadores.infrastructure.ftp.ftplib_db3_downloader import FtplibDb3Downloader
from src.modules.contadores.infrastructure.repositories.sqlalchemy_ftp_client_repository import (
    SqlAlchemyFtpClientRepository,
)
from src.modules.contadores.infrastructure.sqlite.sqlite3_db3_file_reader import (
    Sqlite3Db3FileReader,
)
from src.modules.contadores.presentation.dependencies import get_grupos_economicos_ftp_gateway
from src.modules.contadores.presentation.schemas.ftp_client_schemas import (
    FtpClientIn,
    FtpClientOut,
    GrupoEconomicoFtpOut,
    ProcessFtpClientRequest,
    ProcessFtpClientResponse,
)
from src.modules.contadores.presentation.upload_storage import output_dir
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores/ftp", tags=["contadores-ftp"])

_require_export = Depends(require_permission(EXPORT))
_grupos = Depends(get_grupos_economicos_ftp_gateway)
# Ver el mismo comentario en sds_router.py: el frontend carga todo el
# catálogo en un combobox con búsqueda en vivo, no una tabla paginada — el
# default grande cubre eso sin dejar de cumplir el contrato de paginación
# (hay ~230 clientes FTP reales, ver INTEGRACION_APPS_PLAN.md).
_MAX_PAGE_SIZE = 2000


@router.get("/clients", response_model=Page[FtpClientOut])
async def list_ftp_clients(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=1000, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[FtpClientOut]:
    """Lista todos los clientes FTP ordenados por nombre."""
    repo = SqlAlchemyFtpClientRepository(db)
    results = await ListFtpClientsUseCase(repo).execute()
    return Page.of([FtpClientOut.from_result(r) for r in results], page=page, size=size)


@router.get("/grupos-economicos", response_model=Page[GrupoEconomicoFtpOut])
async def list_grupos_economicos_ftp(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=1000, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_export,
    grupos: GruposEconomicosFtpGateway = _grupos,
) -> Page[GrupoEconomicoFtpOut]:
    """Grupos económicos de Siges con usuario FTP, para el combobox del alta."""
    items = [
        GrupoEconomicoFtpOut(id=g.id, descripcion=g.descripcion, usuario=g.usuario)
        for g in await grupos.listar()
    ]
    return Page.of(items, page=page, size=size)


@router.post("/clients", response_model=FtpClientOut, status_code=201)
async def create_ftp_client(
    body: FtpClientIn,
    _: Identity = _require_export,
    grupos: GruposEconomicosFtpGateway = _grupos,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> FtpClientOut:
    """Crea un cliente FTP vinculado a un grupo económico de Siges."""
    caso = CreateFtpClientUseCase(
        SqlAlchemyFtpClientRepository(db), grupos, get_settings().contadores_ftp_host
    )
    return FtpClientOut.from_result(await caso.execute(_to_app_request(body)))


@router.get("/clients/{client_id}", response_model=FtpClientOut)
async def get_ftp_client(
    client_id: uuid.UUID,
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> FtpClientOut:
    """Devuelve un cliente FTP por ID."""
    repo = SqlAlchemyFtpClientRepository(db)
    result = await GetFtpClientUseCase(repo).execute(client_id)
    return FtpClientOut.from_result(result)


@router.put("/clients/{client_id}", response_model=FtpClientOut)
async def update_ftp_client(
    client_id: uuid.UUID,
    body: FtpClientIn,
    _: Identity = _require_export,
    grupos: GruposEconomicosFtpGateway = _grupos,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> FtpClientOut:
    """Edita nombre/carpeta/patrón o vincula el cliente a un grupo económico."""
    caso = UpdateFtpClientUseCase(SqlAlchemyFtpClientRepository(db), grupos)
    return FtpClientOut.from_result(await caso.execute(client_id, _to_app_request(body)))


@router.delete("/clients/{client_id}", status_code=204)
async def delete_ftp_client(
    client_id: uuid.UUID,
    _: Identity = _require_export,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    """Elimina un cliente FTP."""
    repo = SqlAlchemyFtpClientRepository(db)
    await DeleteFtpClientUseCase(repo).execute(client_id)


@router.post("/clients/{client_id}/process", response_model=ProcessFtpClientResponse)
async def process_ftp_client(
    client_id: uuid.UUID,
    body: ProcessFtpClientRequest,
    _: Identity = _require_export,
    grupos: GruposEconomicosFtpGateway = _grupos,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ProcessFtpClientResponse:
    """Descarga el DB3 más reciente del cliente vía FTP y genera el CSV de exportación.

    El DB3 descargado (fusionado si había varios archivos del mismo día) se
    guarda en `output_dir` junto al CSV y queda disponible para descarga.
    """
    repo = SqlAlchemyFtpClientRepository(db)
    downloader = FtplibDb3Downloader()
    db3_use_case = RunDb3ExportUseCase(Sqlite3Db3FileReader(), CsvDb3Writer())

    request = DownloadFtpDb3Request(
        client_id=str(client_id),
        output_dir=output_dir(),
        fecha_maxima=body.fecha_maxima,
    )
    caso = DownloadAndProcessFtpDb3UseCase(repo, downloader, db3_use_case, grupos)
    result = await caso.execute(request)
    return ProcessFtpClientResponse.from_result(result)


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _to_app_request(body: FtpClientIn) -> FtpClientRequest:
    return FtpClientRequest(
        name=body.name,
        grupo_economico_id=body.grupo_economico_id,
        path=body.path,
        pattern=body.pattern,
    )
