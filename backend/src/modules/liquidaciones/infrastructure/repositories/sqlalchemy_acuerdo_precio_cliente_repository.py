"""Implementación Postgres del puerto AcuerdoPrecioClienteRepository."""

import dataclasses
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.acuerdo_precio_cliente import (
    AcuerdoPrecioCliente,
)
from src.modules.liquidaciones.domain.value_objects.acuerdo_precio_datos import (
    AcuerdoPrecioDatos,
)
from src.modules.liquidaciones.infrastructure.models.acuerdo_precio_cliente_model import (
    AcuerdoPrecioClienteModel,
)


class SqlAlchemyAcuerdoPrecioClienteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, acuerdo_id: UUID) -> AcuerdoPrecioCliente | None:
        row = await self._session.get(AcuerdoPrecioClienteModel, acuerdo_id)
        return _to_entity(row) if row else None

    async def list_by_prestador(self, prestador_id: UUID) -> list[AcuerdoPrecioCliente]:
        stmt = (
            select(AcuerdoPrecioClienteModel)
            .where(AcuerdoPrecioClienteModel.prestador_id == prestador_id)
            .order_by(
                AcuerdoPrecioClienteModel.empresa_nombre,
                AcuerdoPrecioClienteModel.tipo_servicio,
                AcuerdoPrecioClienteModel.vigencia_desde.desc(),
                AcuerdoPrecioClienteModel.id,
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def create(self, prestador_id: UUID, datos: AcuerdoPrecioDatos) -> AcuerdoPrecioCliente:
        model = AcuerdoPrecioClienteModel(
            id=uuid.uuid4(), prestador_id=prestador_id, **dataclasses.asdict(datos)
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, acuerdo_id: UUID, datos: AcuerdoPrecioDatos
    ) -> AcuerdoPrecioCliente | None:
        row = await self._session.get(AcuerdoPrecioClienteModel, acuerdo_id)
        if row is None:
            return None
        for campo, valor in dataclasses.asdict(datos).items():
            setattr(row, campo, valor)
        await self._session.flush()
        return _to_entity(row)

    async def delete(self, acuerdo_id: UUID) -> bool:
        row = await self._session.get(AcuerdoPrecioClienteModel, acuerdo_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


def _to_entity(row: AcuerdoPrecioClienteModel) -> AcuerdoPrecioCliente:
    return AcuerdoPrecioCliente(
        id=row.id,
        prestador_id=row.prestador_id,
        empresa_nombre=row.empresa_nombre,
        tipo_servicio=row.tipo_servicio,
        factor=row.factor,
        precio_fijo=row.precio_fijo,
        motivo=row.motivo,
        vigencia_desde=row.vigencia_desde,
        vigencia_hasta=row.vigencia_hasta,
        created_at=row.created_at,
    )
