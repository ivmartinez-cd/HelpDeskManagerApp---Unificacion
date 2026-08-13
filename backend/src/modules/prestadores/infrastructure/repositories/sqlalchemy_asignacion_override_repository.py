import uuid
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.infrastructure.models.prestador_models import (
    PrestadorAsignacionOverrideModel,
    PrestadorAsignacionOverridePrestadorModel,
)


class SqlAlchemyAsignacionOverrideRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, override: AsignacionOverride) -> None:
        alcance_total = override.alcance == "TOTAL"
        model = PrestadorAsignacionOverrideModel(
            id=override.id,
            operador_ausente_id=override.operador_ausente_id,
            operador_reemplazante_id=override.operador_reemplazante_id,
            desde=override.desde,
            hasta=override.hasta,
            alcance_total=alcance_total,
            estado=override.estado,
            motivo=override.motivo,
            created_by_user_id=override.created_by_user_id,
        )
        if not alcance_total:
            model.prestadores = [
                PrestadorAsignacionOverridePrestadorModel(prestador_id=pid)
                for pid in override.alcance
            ]
        self._session.add(model)
        await self._session.flush()

    async def list_all(self) -> list[AsignacionOverride]:
        stmt = select(PrestadorAsignacionOverrideModel).options(
            selectinload(PrestadorAsignacionOverrideModel.prestadores)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_id(self, override_id: uuid.UUID) -> AsignacionOverride | None:
        stmt = (
            select(PrestadorAsignacionOverrideModel)
            .options(selectinload(PrestadorAsignacionOverrideModel.prestadores))
            .where(PrestadorAsignacionOverrideModel.id == override_id)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row is not None else None

    async def list_activos_por_ausente(
        self, operador_ausente_id: uuid.UUID
    ) -> list[AsignacionOverride]:
        stmt = (
            select(PrestadorAsignacionOverrideModel)
            .options(selectinload(PrestadorAsignacionOverrideModel.prestadores))
            .where(
                PrestadorAsignacionOverrideModel.operador_ausente_id == operador_ausente_id,
                PrestadorAsignacionOverrideModel.estado == "ACTIVA",
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activos_por_reemplazante(
        self, operador_reemplazante_id: uuid.UUID
    ) -> list[AsignacionOverride]:
        stmt = (
            select(PrestadorAsignacionOverrideModel)
            .options(selectinload(PrestadorAsignacionOverrideModel.prestadores))
            .where(
                PrestadorAsignacionOverrideModel.operador_reemplazante_id
                == operador_reemplazante_id,
                PrestadorAsignacionOverrideModel.estado == "ACTIVA",
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def cancelar(self, override_id: uuid.UUID) -> None:
        stmt = select(PrestadorAsignacionOverrideModel).where(
            PrestadorAsignacionOverrideModel.id == override_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is not None:
            row.estado = "CANCELADA"
            await self._session.flush()


def _to_entity(model: PrestadorAsignacionOverrideModel) -> AsignacionOverride:
    alcance: Literal["TOTAL"] | frozenset[uuid.UUID] = (
        "TOTAL"
        if model.alcance_total
        else frozenset(p.prestador_id for p in model.prestadores)
    )
    # `estado` es String(20) a nivel de columna (sin enum en DB), pero el
    # dominio solo escribe estos dos valores (ver create/cancelar) — cast
    # seguro, no una validación real de la fila.
    estado = cast('Literal["ACTIVA", "CANCELADA"]', model.estado)
    return AsignacionOverride(
        id=model.id,
        operador_ausente_id=model.operador_ausente_id,
        operador_reemplazante_id=model.operador_reemplazante_id,
        desde=model.desde,
        hasta=model.hasta,
        alcance=alcance,
        estado=estado,
        motivo=model.motivo,
        created_by_user_id=model.created_by_user_id,
    )
