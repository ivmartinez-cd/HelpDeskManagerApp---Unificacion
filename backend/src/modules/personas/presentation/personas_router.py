"""Personas (ADR-040): una sola lista de gente — ficha de empleado + acceso
opcional a la app. Los datos laborales se siguen editando por
`/api/vacaciones/empleados`; acá van nombre/mail/color y el acceso."""

import uuid
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity, PermissionView
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.personas.application.use_cases.actualizar_datos_persona import (
    ActualizarDatosPersona,
)
from src.modules.personas.application.use_cases.consultar_personas import (
    ListarPersonas,
    ObtenerPersona,
)
from src.modules.personas.application.use_cases.gestionar_acceso import DarAcceso, QuitarAcceso
from src.modules.personas.domain.entities.persona import Persona
from src.modules.personas.domain.repositories.persona_repository import (
    CampoOrdenPersonas,
    FiltrosPersonas,
    OrdenPersonas,
)
from src.modules.personas.domain.well_known_permissions import MANAGE, UPDATE, VIEW
from src.modules.personas.presentation import dependencies as armado
from src.modules.personas.presentation.schemas.persona_schemas import (
    DatosPersonaRequest,
    PersonaResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/personas", tags=["personas"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_require_manage = Depends(require_permission(MANAGE))
_MANAGE_VIEW = PermissionView(module=MANAGE.module.value, action=MANAGE.action.value)
_MAX_PAGE_SIZE = 200


@router.get("")
async def list_personas(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    q: str | None = Query(default=None),
    sector_id: uuid.UUID | None = Query(default=None, alias="sectorId"),
    activa: bool | None = Query(default=None),
    entra_a_la_app: bool | None = Query(default=None, alias="entraALaApp"),
    sort_by: CampoOrdenPersonas = Query(default="nombre", alias="sortBy"),
    sort_dir: Literal["asc", "desc"] = Query(default="asc", alias="sortDir"),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[PersonaResponse]:
    filtros = FiltrosPersonas(
        busqueda=q, sector_id=sector_id, activa=activa, entra_a_la_app=entra_a_la_app
    )
    orden = OrdenPersonas(campo=sort_by, descendente=sort_dir == "desc")
    personas, total = await ListarPersonas(armado.repositorio(db)).execute(
        filtros, orden, page=page, size=size
    )
    return _pagina(personas, total, page, size)


def _pagina(personas: list[Persona], total: int, page: int, size: int) -> Page[PersonaResponse]:
    items = [PersonaResponse.from_entity(p) for p in personas]
    return Page(items=items, total=total, page=page, size=size)


@router.get("/{persona_id}")
async def get_persona(
    persona_id: uuid.UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PersonaResponse:
    persona = await ObtenerPersona(armado.repositorio(db)).execute(persona_id)
    return PersonaResponse.from_entity(persona)


@router.patch("/{persona_id}/datos")
async def update_datos(
    persona_id: uuid.UUID,
    body: DatosPersonaRequest,
    identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PersonaResponse:
    puede_gestionar = identity.user.is_superadmin or _MANAGE_VIEW in identity.permissions
    persona = await ActualizarDatosPersona(armado.deps_datos(db, identity.user.id)).execute(
        persona_id, body.to_datos(), puede_gestionar_acceso=puede_gestionar
    )
    return PersonaResponse.from_entity(persona)


@router.post("/{persona_id}/acceso")
async def dar_acceso(
    persona_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PersonaResponse:
    deps = armado.deps_acceso(db, identity.user.id, background_tasks)
    return PersonaResponse.from_entity(await DarAcceso(deps).execute(persona_id))


@router.delete("/{persona_id}/acceso")
async def quitar_acceso(
    persona_id: uuid.UUID,
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PersonaResponse:
    caso = QuitarAcceso(armado.repositorio(db), armado.cuentas(db))
    return PersonaResponse.from_entity(await caso.execute(persona_id))
