import uuid
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    TurnoAsignacionOverride,
)
from src.modules.turnos.infrastructure.models.turno_models import (
    TurnoAsignacionOverrideModel,
    TurnoAsignacionOverrideSlotModel,
)
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride


class SqlAlchemyAsignacionOverrideRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, override: TurnoAsignacionOverride) -> None:
        alcance_total = override.alcance == "TOTAL"
        model = TurnoAsignacionOverrideModel(
            id=override.id,
            operador_ausente_id=override.operador_ausente_id,
            operador_reemplazante_id=override.operador_reemplazante_id,
            desde=override.desde,
            hasta=override.hasta,
            alcance_total=alcance_total,
            estado=override.estado,
            motivo=override.motivo,
            created_by_user_id=override.created_by_user_id,
            intercambio_id=override.intercambio_id,
        )
        if not alcance_total:
            model.slots = [
                TurnoAsignacionOverrideSlotModel(slot_id=sid) for sid in override.alcance
            ]
        self._session.add(model)
        await self._session.flush()

    async def list_all(self) -> list[TurnoAsignacionOverride]:
        stmt = select(TurnoAsignacionOverrideModel).options(
            selectinload(TurnoAsignacionOverrideModel.slots)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_id(self, override_id: uuid.UUID) -> TurnoAsignacionOverride | None:
        stmt = (
            select(TurnoAsignacionOverrideModel)
            .options(selectinload(TurnoAsignacionOverrideModel.slots))
            .where(TurnoAsignacionOverrideModel.id == override_id)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row is not None else None

    async def list_activos_por_ausente(
        self, operador_ausente_id: uuid.UUID
    ) -> list[TurnoAsignacionOverride]:
        stmt = (
            select(TurnoAsignacionOverrideModel)
            .options(selectinload(TurnoAsignacionOverrideModel.slots))
            .where(
                TurnoAsignacionOverrideModel.operador_ausente_id == operador_ausente_id,
                TurnoAsignacionOverrideModel.estado == "ACTIVA",
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activos_por_ausentes(
        self, operador_ausente_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[TurnoAsignacionOverride]]:
        if not operador_ausente_ids:
            return {}
        stmt = (
            select(TurnoAsignacionOverrideModel)
            .options(selectinload(TurnoAsignacionOverrideModel.slots))
            .where(
                TurnoAsignacionOverrideModel.operador_ausente_id.in_(operador_ausente_ids),
                TurnoAsignacionOverrideModel.estado == "ACTIVA",
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        grouped: dict[uuid.UUID, list[TurnoAsignacionOverride]] = {}
        for r in rows:
            grouped.setdefault(r.operador_ausente_id, []).append(_to_entity(r))
        return grouped

    async def list_by_intercambio(
        self, intercambio_id: uuid.UUID
    ) -> list[TurnoAsignacionOverride]:
        stmt = (
            select(TurnoAsignacionOverrideModel)
            .options(selectinload(TurnoAsignacionOverrideModel.slots))
            .where(TurnoAsignacionOverrideModel.intercambio_id == intercambio_id)
            .order_by(TurnoAsignacionOverrideModel.id)  # solo determinismo, sin semántica
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def update(self, override: TurnoAsignacionOverride) -> None:
        stmt = (
            select(TurnoAsignacionOverrideModel)
            .options(selectinload(TurnoAsignacionOverrideModel.slots))
            .where(TurnoAsignacionOverrideModel.id == override.id)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return
        row.operador_ausente_id = override.operador_ausente_id
        row.operador_reemplazante_id = override.operador_reemplazante_id
        row.desde = override.desde
        row.hasta = override.hasta
        row.alcance_total = override.alcance == "TOTAL"
        row.motivo = override.motivo
        # Dos flushes: delete-orphan borra las hijas viejas antes de insertar
        # las nuevas -- pueden compartir PK (p. ej. si solo cambian las
        # fechas) y en un único flush el INSERT se ejecuta antes que el
        # DELETE (mismo motivo que el flush explícito en
        # SqlAlchemyAsignacionRepository.replace_for_slot).
        row.slots = []
        await self._session.flush()
        if override.alcance != "TOTAL":
            row.slots = [
                TurnoAsignacionOverrideSlotModel(slot_id=sid) for sid in override.alcance
            ]
            await self._session.flush()

    async def cancelar(self, override_id: uuid.UUID) -> None:
        stmt = select(TurnoAsignacionOverrideModel).where(
            TurnoAsignacionOverrideModel.id == override_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is not None:
            row.estado = "CANCELADA"
            await self._session.flush()


def _to_entity(model: TurnoAsignacionOverrideModel) -> TurnoAsignacionOverride:
    alcance: Literal["TOTAL"] | frozenset[uuid.UUID] = (
        "TOTAL" if model.alcance_total else frozenset(s.slot_id for s in model.slots)
    )
    # `estado` es String(20) a nivel de columna (sin enum en DB), pero el
    # dominio solo escribe estos dos valores (ver create/cancelar) -- cast
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
        intercambio_id=model.intercambio_id,
    )
