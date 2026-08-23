from collections.abc import Sequence

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.preventivos.infrastructure.models.sucursal_coordenadas_model import (
    SucursalCoordenadasModel,
)


class SqlAlchemySucursalCoordenadasRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_siges_sucursal_ids(
        self, siges_sucursal_ids: Sequence[int]
    ) -> dict[int, SucursalCoordenadas]:
        if not siges_sucursal_ids:
            return {}
        stmt = select(SucursalCoordenadasModel).where(
            SucursalCoordenadasModel.siges_sucursal_id.in_(list(siges_sucursal_ids))
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return {r.siges_sucursal_id: _to_entity(r) for r in rows}

    async def upsert(self, coordenadas: SucursalCoordenadas) -> None:
        row = await self._row(coordenadas.siges_sucursal_id)
        if row is None:
            self._session.add(_to_model(coordenadas))
        else:
            _actualizar(row, coordenadas)
        await self._session.flush()

    async def delete(self, siges_sucursal_id: int) -> None:
        stmt = sa_delete(SucursalCoordenadasModel).where(
            SucursalCoordenadasModel.siges_sucursal_id == siges_sucursal_id
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def _row(self, siges_sucursal_id: int) -> SucursalCoordenadasModel | None:
        stmt = select(SucursalCoordenadasModel).where(
            SucursalCoordenadasModel.siges_sucursal_id == siges_sucursal_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()


def _to_entity(model: SucursalCoordenadasModel) -> SucursalCoordenadas:
    return SucursalCoordenadas(
        siges_sucursal_id=model.siges_sucursal_id,
        latitud=model.latitud,
        longitud=model.longitud,
        formatted_address=model.formatted_address,
        fecha_resolucion=model.fecha_resolucion,
        corregido_por_user_id=model.corregido_por_user_id,
        corregido_por_nombre=model.corregido_por_nombre,
        nota=model.nota,
    )


def _to_model(coordenadas: SucursalCoordenadas) -> SucursalCoordenadasModel:
    return SucursalCoordenadasModel(
        siges_sucursal_id=coordenadas.siges_sucursal_id,
        latitud=coordenadas.latitud,
        longitud=coordenadas.longitud,
        formatted_address=coordenadas.formatted_address,
        fecha_resolucion=coordenadas.fecha_resolucion,
        corregido_por_user_id=coordenadas.corregido_por_user_id,
        corregido_por_nombre=coordenadas.corregido_por_nombre,
        nota=coordenadas.nota,
    )


def _actualizar(row: SucursalCoordenadasModel, coordenadas: SucursalCoordenadas) -> None:
    row.latitud = coordenadas.latitud
    row.longitud = coordenadas.longitud
    row.formatted_address = coordenadas.formatted_address
    row.fecha_resolucion = coordenadas.fecha_resolucion
    row.corregido_por_user_id = coordenadas.corregido_por_user_id
    row.corregido_por_nombre = coordenadas.corregido_por_nombre
    row.nota = coordenadas.nota
