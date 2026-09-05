"""Endpoints de acuerdos de precio por cliente (/api/liquidaciones/acuerdos).

Cada escritura reanaliza las liquidaciones abiertas del prestador: el acuerdo
cambia el precio esperado de ALT001, así que las alertas de ese cliente se
acomodan solas (mismo criterio que tarifarios y Tabla KM)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.presentation.config_routers._deps import (
    CATALOGO_SIZE,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.config_routers._reanalisis import (
    reanalizar_abiertas,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_create_acuerdo,
    build_delete_acuerdo,
    build_list_acuerdos,
    build_update_acuerdo,
)
from src.modules.liquidaciones.presentation.schemas.acuerdos_schemas import (
    AcuerdoIn,
    AcuerdoOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/acuerdos", response_model=Page[AcuerdoOut])
async def list_acuerdos(
    prestador_id: UUID = Query(alias="prestadorId"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[AcuerdoOut]:
    rows = await build_list_acuerdos(db).execute(prestador_id)
    return Page.of([AcuerdoOut.from_entity(a) for a in rows], page=page, size=size)


@router.post("/acuerdos", response_model=AcuerdoOut, status_code=201)
async def create_acuerdo(
    body: AcuerdoIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AcuerdoOut:
    acuerdo = await build_create_acuerdo(db).execute(body.prestador_id, body.to_datos())
    await reanalizar_abiertas(db, acuerdo.prestador_id)
    return AcuerdoOut.from_entity(acuerdo)


@router.patch("/acuerdos/{acuerdo_id}", response_model=AcuerdoOut)
async def update_acuerdo(
    acuerdo_id: UUID,
    body: AcuerdoIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AcuerdoOut:
    acuerdo = await build_update_acuerdo(db).execute(acuerdo_id, body.to_datos())
    await reanalizar_abiertas(db, acuerdo.prestador_id)
    return AcuerdoOut.from_entity(acuerdo)


@router.delete("/acuerdos/{acuerdo_id}", status_code=204)
async def delete_acuerdo(
    acuerdo_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    borrado = await build_delete_acuerdo(db).execute(acuerdo_id)
    await reanalizar_abiertas(db, borrado.prestador_id)
