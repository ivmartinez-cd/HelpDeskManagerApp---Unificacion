from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.preventivos.domain.entities.habilitacion_preventivo import (
    HabilitacionPreventivo,
)
from src.modules.preventivos.infrastructure.models.habilitacion_model import (
    HabilitacionPreventivoModel,
)


class SqlAlchemyHabilitacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_activa(self, siges_maquina_id: int) -> HabilitacionPreventivo | None:
        row = await self._row_activa(siges_maquina_id)
        return _to_entity(row) if row is not None else None

    async def list_activas_por_maquinas(
        self, siges_maquina_ids: Sequence[int]
    ) -> list[HabilitacionPreventivo]:
        if not siges_maquina_ids:
            return []
        stmt = select(HabilitacionPreventivoModel).where(
            HabilitacionPreventivoModel.activa.is_(True),
            HabilitacionPreventivoModel.siges_maquina_id.in_(list(siges_maquina_ids)),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def create(self, habilitacion: HabilitacionPreventivo) -> None:
        self._session.add(
            HabilitacionPreventivoModel(
                id=habilitacion.id,
                siges_maquina_id=habilitacion.siges_maquina_id,
                habilitado_por_user_id=habilitacion.habilitado_por_user_id,
                habilitado_por_nombre=habilitacion.habilitado_por_nombre,
                habilitado_en=habilitacion.habilitado_en,
                nota=habilitacion.nota,
                activa=habilitacion.activa,
                deshabilitado_en=habilitacion.deshabilitado_en,
                deshabilitado_por=habilitacion.deshabilitado_por,
            )
        )
        await self._session.flush()

    async def desactivar(
        self,
        siges_maquina_id: int,
        *,
        deshabilitado_por: str,
        deshabilitado_en: datetime,
    ) -> bool:
        row = await self._row_activa(siges_maquina_id)
        if row is None:
            return False
        row.activa = False
        row.deshabilitado_por = deshabilitado_por
        row.deshabilitado_en = deshabilitado_en
        await self._session.flush()
        return True

    async def _row_activa(self, siges_maquina_id: int) -> HabilitacionPreventivoModel | None:
        stmt = select(HabilitacionPreventivoModel).where(
            HabilitacionPreventivoModel.siges_maquina_id == siges_maquina_id,
            HabilitacionPreventivoModel.activa.is_(True),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()


def _to_entity(model: HabilitacionPreventivoModel) -> HabilitacionPreventivo:
    return HabilitacionPreventivo(
        id=model.id,
        siges_maquina_id=model.siges_maquina_id,
        habilitado_por_user_id=model.habilitado_por_user_id,
        habilitado_por_nombre=model.habilitado_por_nombre,
        habilitado_en=model.habilitado_en,
        nota=model.nota,
        activa=model.activa,
        deshabilitado_en=model.deshabilitado_en,
        deshabilitado_por=model.deshabilitado_por,
    )
