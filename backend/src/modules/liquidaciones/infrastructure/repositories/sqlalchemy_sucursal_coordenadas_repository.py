"""Implementación Postgres del puerto SucursalCoordenadasRepository."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.liquidaciones.infrastructure.models.geolocalizacion_models import (
    SucursalCoordenadasModel,
)


class SqlAlchemySucursalCoordenadasRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_prestador(self, prestador_id: UUID) -> list[SucursalCoordenadas]:
        stmt = (
            select(SucursalCoordenadasModel)
            .where(SucursalCoordenadasModel.prestador_id == prestador_id)
            .order_by(
                SucursalCoordenadasModel.empresa_nombre,
                SucursalCoordenadasModel.sucursal_nombre,
                SucursalCoordenadasModel.id,
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def get_by_siges_sucursal_id(
        self, siges_sucursal_id: int
    ) -> SucursalCoordenadas | None:
        row = await self._get_model(siges_sucursal_id)
        return _to_entity(row) if row else None

    async def upsert_pendiente(
        self,
        *,
        prestador_id: UUID,
        siges_sucursal_id: int,
        empresa_nombre: str,
        sucursal_nombre: str,
        direccion_normalizada: str | None,
    ) -> SucursalCoordenadas:
        row = await self._get_model(siges_sucursal_id)
        if row is None:
            row = SucursalCoordenadasModel(
                prestador_id=prestador_id, siges_sucursal_id=siges_sucursal_id
            )
            self._session.add(row)
        row.prestador_id = prestador_id
        row.empresa_nombre = empresa_nombre
        row.sucursal_nombre = sucursal_nombre
        row.direccion_normalizada = direccion_normalizada
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def resolver(
        self,
        siges_sucursal_id: int,
        *,
        latitud: float,
        longitud: float,
        procedencia: str,
        formatted_address: str | None,
    ) -> SucursalCoordenadas | None:
        row = await self._get_model(siges_sucursal_id)
        if row is None:
            return None
        row.latitud = latitud
        row.longitud = longitud
        row.procedencia = procedencia
        row.formatted_address = formatted_address
        row.fecha_resolucion = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def _get_model(self, siges_sucursal_id: int) -> SucursalCoordenadasModel | None:
        stmt = select(SucursalCoordenadasModel).where(
            SucursalCoordenadasModel.siges_sucursal_id == siges_sucursal_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()


def _to_entity(row: SucursalCoordenadasModel) -> SucursalCoordenadas:
    return SucursalCoordenadas(
        id=row.id,
        prestador_id=row.prestador_id,
        siges_sucursal_id=row.siges_sucursal_id,
        empresa_nombre=row.empresa_nombre,
        sucursal_nombre=row.sucursal_nombre,
        direccion_normalizada=row.direccion_normalizada,
        latitud=row.latitud,
        longitud=row.longitud,
        procedencia=row.procedencia,
        formatted_address=row.formatted_address,
        fecha_resolucion=row.fecha_resolucion,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
