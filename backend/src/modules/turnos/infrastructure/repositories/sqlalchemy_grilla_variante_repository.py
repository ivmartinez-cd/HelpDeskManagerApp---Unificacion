import uuid
from datetime import date
from typing import cast

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.turnos.domain.entities.grilla_variante import (
    EstadoVariante,
    GrillaVariante,
    VarianteSlot,
)
from src.modules.turnos.infrastructure.models.grilla_variante_models import (
    TurnoGrillaVarianteAsignacionModel,
    TurnoGrillaVarianteModel,
    TurnoGrillaVarianteSlotModel,
)


class SqlAlchemyGrillaVarianteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, variante: GrillaVariante) -> None:
        model = TurnoGrillaVarianteModel(
            id=variante.id,
            motivo=variante.motivo,
            origen_texto=variante.origen_texto,
            desde=variante.desde,
            hasta=variante.hasta,
            estado=variante.estado,
            created_by_user_id=variante.created_by_user_id,
            slots=[_to_slot_model(s) for s in variante.slots],
        )
        self._session.add(model)
        await self._session.flush()

    async def update(self, variante: GrillaVariante) -> None:
        row = (await self._session.execute(_query().where(
            TurnoGrillaVarianteModel.id == variante.id
        ))).scalar_one_or_none()
        if row is None:
            return
        row.motivo = variante.motivo
        row.origen_texto = variante.origen_texto
        row.desde = variante.desde
        row.hasta = variante.hasta
        # Dos flushes: delete-orphan borra las franjas viejas antes de insertar
        # las nuevas (mismo motivo que SqlAlchemyAsignacionOverrideRepository.update).
        row.slots = []
        await self._session.flush()
        row.slots = [_to_slot_model(s) for s in variante.slots]
        await self._session.flush()

    async def get_by_id(self, variante_id: uuid.UUID) -> GrillaVariante | None:
        row = (await self._session.execute(_query().where(
            TurnoGrillaVarianteModel.id == variante_id
        ))).scalar_one_or_none()
        return _to_entity(row) if row is not None else None

    async def list_all(self) -> list[GrillaVariante]:
        rows = (await self._session.execute(_query())).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activas(self) -> list[GrillaVariante]:
        stmt = _query().where(TurnoGrillaVarianteModel.estado == "ACTIVA")
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def find_vigente(self, fecha: date) -> GrillaVariante | None:
        stmt = (
            _query()
            .where(
                TurnoGrillaVarianteModel.estado == "ACTIVA",
                TurnoGrillaVarianteModel.desde <= fecha,
                TurnoGrillaVarianteModel.hasta >= fecha,
            )
            .order_by(TurnoGrillaVarianteModel.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row is not None else None

    async def cancelar(self, variante_id: uuid.UUID) -> None:
        row = await self._session.get(TurnoGrillaVarianteModel, variante_id)
        if row is not None:
            row.estado = "CANCELADA"
            await self._session.flush()


def _query() -> Select[tuple[TurnoGrillaVarianteModel]]:
    return select(TurnoGrillaVarianteModel).options(
        selectinload(TurnoGrillaVarianteModel.slots).selectinload(
            TurnoGrillaVarianteSlotModel.asignaciones
        )
    )


def _to_slot_model(slot: VarianteSlot) -> TurnoGrillaVarianteSlotModel:
    return TurnoGrillaVarianteSlotModel(
        id=slot.id,
        casilla_id=slot.casilla_id,
        dia_semana=slot.dia_semana,
        hora_inicio=slot.hora_inicio,
        hora_fin=slot.hora_fin,
        sort_order=slot.sort_order,
        asignaciones=[
            TurnoGrillaVarianteAsignacionModel(user_id=u) for u in dict.fromkeys(slot.user_ids)
        ],
    )


def _to_entity(model: TurnoGrillaVarianteModel) -> GrillaVariante:
    return GrillaVariante(
        id=model.id,
        motivo=model.motivo,
        origen_texto=model.origen_texto,
        desde=model.desde,
        hasta=model.hasta,
        # String(20) + CHECK en DB: el dominio solo escribe estos dos valores.
        estado=cast(EstadoVariante, model.estado),
        created_by_user_id=model.created_by_user_id,
        slots=[
            VarianteSlot(
                id=s.id,
                casilla_id=s.casilla_id,
                dia_semana=s.dia_semana,
                hora_inicio=s.hora_inicio,
                hora_fin=s.hora_fin,
                sort_order=s.sort_order,
                user_ids=[a.user_id for a in s.asignaciones],
            )
            for s in sorted(model.slots, key=lambda s: (s.dia_semana, s.hora_inicio, s.sort_order))
        ],
    )
