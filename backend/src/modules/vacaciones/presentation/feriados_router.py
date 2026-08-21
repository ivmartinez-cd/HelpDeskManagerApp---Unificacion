import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.application.use_cases.gestionar_feriados import (
    CreateFeriado,
    DeleteFeriado,
    GestionFeriadosDependencies,
    ImportarFeriados,
    ImportarFeriadosDependencies,
    ListFeriados,
    UpdateFeriado,
)
from src.modules.vacaciones.domain.well_known_permissions import MANAGE, VIEW
from src.modules.vacaciones.infrastructure.argentinadatos_feriados_client import (
    ArgentinaDatosFeriadosClient,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_auditoria import (
    SqlAlchemyRegistradorAuditoria,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_feriado_repository import (
    SqlAlchemyFeriadoRepository,
)
from src.modules.vacaciones.presentation.schemas.catalogo_schemas import (
    FeriadoRequest,
    FeriadoResponse,
    ImportFeriadosResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones/feriados", tags=["vacaciones"])

_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


def _deps(
    db: AsyncSession, identity: Identity | None = None
) -> GestionFeriadosDependencies:
    return GestionFeriadosDependencies(
        feriados=SqlAlchemyFeriadoRepository(db),
        auditoria=SqlAlchemyRegistradorAuditoria(
            db, identity.user.id if identity else None
        ),
    )


@router.get("")
async def list_feriados(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[FeriadoResponse]:
    feriados = await ListFeriados(_deps(db)).execute()
    return Page.of([FeriadoResponse.from_entity(f) for f in feriados], page=page, size=size)


@router.get("/publicos")
async def list_feriados_publicos(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[FeriadoResponse]:
    """Fecha y nombre del feriado, sin permiso de vacaciones: la información
    es pública (calendario nacional), la usan otros módulos (Home/Contadores)
    para tener en cuenta feriados en sus propios cálculos."""
    feriados = await ListFeriados(_deps(db)).execute()
    return Page.of([FeriadoResponse.from_entity(f) for f in feriados], page=page, size=size)


@router.get("/export")
async def export_feriados(
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> JSONResponse:
    """Backup JSON descargable (paridad con el export del legacy)."""
    feriados = await ListFeriados(_deps(db)).execute()
    payload = [
        FeriadoResponse.from_entity(f).model_dump(by_alias=True, mode="json")
        for f in feriados
    ]
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": 'attachment; filename="feriados-backup.json"'},
    )


@router.post("/importar/{year}")
async def importar_feriados(
    year: int,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ImportFeriadosResponse:
    deps = ImportarFeriadosDependencies(
        feriados=SqlAlchemyFeriadoRepository(db),
        provider=ArgentinaDatosFeriadosClient(),
        auditoria=SqlAlchemyRegistradorAuditoria(db, identity.user.id),
    )
    resultado = await ImportarFeriados(deps).execute(year)
    return ImportFeriadosResponse.from_dto(resultado)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_feriado(
    body: FeriadoRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> FeriadoResponse:
    feriado = await CreateFeriado(_deps(db, identity)).execute(body.to_command())
    return FeriadoResponse.from_entity(feriado)


@router.put("/{feriado_id}")
async def update_feriado(
    feriado_id: uuid.UUID,
    body: FeriadoRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> FeriadoResponse:
    feriado = await UpdateFeriado(_deps(db, identity)).execute(
        feriado_id, body.to_command()
    )
    return FeriadoResponse.from_entity(feriado)


@router.delete("/{feriado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feriado(
    feriado_id: uuid.UUID,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await DeleteFeriado(_deps(db, identity)).execute(feriado_id)
