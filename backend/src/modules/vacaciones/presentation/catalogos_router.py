import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.application.use_cases.gestionar_cargos import (
    CreateCargo,
    DeleteCargo,
    GestionCargosDependencies,
    ListCargos,
    UpdateCargo,
)
from src.modules.vacaciones.application.use_cases.gestionar_sectores import (
    CreateSector,
    DeleteSector,
    GestionSectoresDependencies,
    ListSectores,
    UpdateSector,
)
from src.modules.vacaciones.domain.well_known_permissions import MANAGE, VIEW
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_cargo_repository import (
    SqlAlchemyCargoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_manager_repository import (  # noqa: E501
    SqlAlchemySectorManagerRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_repository import (
    SqlAlchemySectorRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_user_directory import (
    SqlAlchemyUserDirectory,
)
from src.modules.vacaciones.presentation.schemas.catalogo_schemas import (
    CargoRequest,
    CargoResponse,
    JefeSectorResponse,
    SectorRequest,
    SectorResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones", tags=["vacaciones"])

_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


def _sector_deps(db: AsyncSession) -> GestionSectoresDependencies:
    return GestionSectoresDependencies(
        sectores=SqlAlchemySectorRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        sector_manager=SqlAlchemySectorManagerRepository(db),
        users=SqlAlchemyUserDirectory(db),
    )


def _cargo_deps(db: AsyncSession) -> GestionCargosDependencies:
    return GestionCargosDependencies(cargos=SqlAlchemyCargoRepository(db))


@router.get("/sectores")
async def list_sectores(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[SectorResponse]:
    sectores = await ListSectores(_sector_deps(db)).execute()
    return Page.of([SectorResponse.from_dto(s) for s in sectores], page=page, size=size)


@router.post("/sectores", status_code=status.HTTP_201_CREATED)
async def create_sector(
    body: SectorRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> dict[str, uuid.UUID]:
    sector = await CreateSector(_sector_deps(db)).execute(body.to_command())
    return {"id": sector.id}


@router.put("/sectores/{sector_id}")
async def update_sector(
    sector_id: uuid.UUID,
    body: SectorRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> dict[str, uuid.UUID]:
    sector = await UpdateSector(_sector_deps(db)).execute(sector_id, body.to_command())
    return {"id": sector.id}


@router.delete("/sectores/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sector(
    sector_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> None:
    await DeleteSector(_sector_deps(db)).execute(sector_id)


@router.get("/usuarios")
async def list_usuarios(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> Page[JefeSectorResponse]:
    """Cuentas activas de la plataforma para los selects de jefe de sector y
    vínculo empleado↔usuario (solo Gestión Humana)."""
    usuarios = await SqlAlchemyUserDirectory(db).list_activos()
    return Page.of(
        [JefeSectorResponse.from_info(u) for u in usuarios], page=page, size=size
    )


@router.get("/cargos")
async def list_cargos(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[CargoResponse]:
    cargos = await ListCargos(_cargo_deps(db)).execute()
    return Page.of([CargoResponse.from_dto(c) for c in cargos], page=page, size=size)


@router.post("/cargos", status_code=status.HTTP_201_CREATED)
async def create_cargo(
    body: CargoRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> dict[str, uuid.UUID]:
    cargo = await CreateCargo(_cargo_deps(db)).execute(body.to_command())
    return {"id": cargo.id}


@router.put("/cargos/{cargo_id}")
async def update_cargo(
    cargo_id: uuid.UUID,
    body: CargoRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> dict[str, uuid.UUID]:
    cargo = await UpdateCargo(_cargo_deps(db)).execute(cargo_id, body.to_command())
    return {"id": cargo.id}


@router.delete("/cargos/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cargo(
    cargo_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> None:
    await DeleteCargo(_cargo_deps(db)).execute(cargo_id)
