import uuid
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.infrastructure.models.asignacion_override_model import (
    AsignacionOverrideClienteModel,
    AsignacionOverrideModel,
)


class SqlAlchemyAsignacionOverrideRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, override: AsignacionOverride) -> None:
        alcance_total = override.alcance == "TOTAL"
        model = AsignacionOverrideModel(
            id=override.id,
            operador_ausente_id=override.operador_ausente_id,
            operador_reemplazante_id=override.operador_reemplazante_id,
            vigente_desde=override.vigente_desde,
            vigente_hasta=override.vigente_hasta,
            alcance_total=alcance_total,
            estado=override.estado,
            motivo=override.motivo,
            created_by_user_id=override.created_by_user_id,
        )
        if not alcance_total:
            model.clientes = [
                AsignacionOverrideClienteModel(cliente=cliente) for cliente in override.alcance
            ]
        self._session.add(model)
        await self._session.flush()

    async def list_all(self) -> list[AsignacionOverride]:
        stmt = select(AsignacionOverrideModel).options(
            selectinload(AsignacionOverrideModel.clientes)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_id(self, override_id: uuid.UUID) -> AsignacionOverride | None:
        stmt = (
            select(AsignacionOverrideModel)
            .options(selectinload(AsignacionOverrideModel.clientes))
            .where(AsignacionOverrideModel.id == override_id)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row is not None else None

    async def list_activos(self) -> list[AsignacionOverride]:
        stmt = (
            select(AsignacionOverrideModel)
            .options(selectinload(AsignacionOverrideModel.clientes))
            .where(AsignacionOverrideModel.estado == "ACTIVA")
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activos_por_ausente(
        self, operador_ausente_id: str
    ) -> list[AsignacionOverride]:
        stmt = (
            select(AsignacionOverrideModel)
            .options(selectinload(AsignacionOverrideModel.clientes))
            .where(
                AsignacionOverrideModel.operador_ausente_id == operador_ausente_id,
                AsignacionOverrideModel.estado == "ACTIVA",
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activos_por_reemplazante(
        self, operador_reemplazante_id: str
    ) -> list[AsignacionOverride]:
        stmt = (
            select(AsignacionOverrideModel)
            .options(selectinload(AsignacionOverrideModel.clientes))
            .where(
                AsignacionOverrideModel.operador_reemplazante_id == operador_reemplazante_id,
                AsignacionOverrideModel.estado == "ACTIVA",
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def update(self, override: AsignacionOverride) -> None:
        stmt = (
            select(AsignacionOverrideModel)
            .options(selectinload(AsignacionOverrideModel.clientes))
            .where(AsignacionOverrideModel.id == override.id)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return
        row.operador_ausente_id = override.operador_ausente_id
        row.operador_reemplazante_id = override.operador_reemplazante_id
        row.vigente_desde = override.vigente_desde
        row.vigente_hasta = override.vigente_hasta
        row.alcance_total = override.alcance == "TOTAL"
        row.motivo = override.motivo
        # Dos flushes: delete-orphan borra las hijas viejas antes de insertar
        # las nuevas — pueden compartir PK (p. ej. si solo cambian las fechas)
        # y en un único flush el INSERT se ejecuta antes que el DELETE.
        row.clientes = []
        await self._session.flush()
        if override.alcance != "TOTAL":
            row.clientes = [
                AsignacionOverrideClienteModel(cliente=cliente) for cliente in override.alcance
            ]
            await self._session.flush()

    async def cancelar(self, override_id: uuid.UUID) -> None:
        stmt = select(AsignacionOverrideModel).where(AsignacionOverrideModel.id == override_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is not None:
            row.estado = "CANCELADA"
            await self._session.flush()


def _to_entity(model: AsignacionOverrideModel) -> AsignacionOverride:
    alcance: Literal["TOTAL"] | frozenset[str] = (
        "TOTAL" if model.alcance_total else frozenset(c.cliente for c in model.clientes)
    )
    # `estado` es String(20) a nivel de columna (sin enum en DB), pero el
    # dominio solo escribe estos dos valores (ver create/cancelar) — cast
    # seguro, no una validación real de la fila.
    estado = cast('Literal["ACTIVA", "CANCELADA"]', model.estado)
    return AsignacionOverride(
        id=model.id,
        operador_ausente_id=model.operador_ausente_id,
        operador_reemplazante_id=model.operador_reemplazante_id,
        vigente_desde=model.vigente_desde,
        vigente_hasta=model.vigente_hasta,
        alcance=alcance,
        estado=estado,
        motivo=model.motivo,
        created_by_user_id=model.created_by_user_id,
    )
