"""Implementación Postgres del puerto TablaKmRepository (tabla tabla_kms)."""

import uuid
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.infrastructure.models.tabla_km_model import TablaKmModel


class SqlAlchemyTablaKmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tabla_km_id: UUID) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        return _to_entity(row) if row else None

    async def list_by_prestador(self, prestador_id: UUID) -> list[TablaKm]:
        stmt = select(TablaKmModel).where(TablaKmModel.prestador_id == prestador_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def list_all(
        self,
        *,
        prestador_id: UUID | None = None,
        q: str | None = None,
    ) -> list[TablaKm]:
        stmt = select(TablaKmModel).order_by(
            TablaKmModel.empresa_nombre, TablaKmModel.sucursal_nombre
        )
        if prestador_id is not None:
            stmt = stmt.where(TablaKmModel.prestador_id == prestador_id)
        if q:
            pattern = f"%{q.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(TablaKmModel.empresa_nombre).like(pattern),
                    func.lower(TablaKmModel.sucursal_nombre).like(pattern),
                )
            )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def update(
        self,
        tabla_km_id: UUID,
        *,
        prestador_id: UUID,
        spst_id: UUID | None,
        empresa_nombre: str,
        sucursal_nombre: str,
        observaciones: str | None,
        domicilio_cliente: str | None,
        localidad_cliente: str | None,
        provincia_cliente: str | None,
        kms_recorrido: float,
        umbral_viatico: float,
        aplica_viatico: bool,
        kms_a_facturar: float,
        url_maps: str | None,
    ) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if row is None:
            return None
        row.prestador_id = prestador_id
        row.spst_id = spst_id
        row.empresa_nombre = empresa_nombre
        row.sucursal_nombre = sucursal_nombre
        row.observaciones = observaciones
        row.domicilio_cliente = domicilio_cliente
        row.localidad_cliente = localidad_cliente
        row.provincia_cliente = provincia_cliente
        row.kms_recorrido = kms_recorrido
        row.umbral_viatico = umbral_viatico
        row.aplica_viatico = aplica_viatico
        row.kms_a_facturar = kms_a_facturar
        row.url_maps = url_maps
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def delete(self, tabla_km_id: UUID) -> bool:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def create(
        self,
        *,
        prestador_id: UUID,
        spst_id: UUID | None,
        empresa_nombre: str,
        sucursal_nombre: str,
        observaciones: str | None,
        domicilio_cliente: str | None,
        localidad_cliente: str | None,
        provincia_cliente: str | None,
        kms_recorrido: float,
        umbral_viatico: float,
        aplica_viatico: bool,
        kms_a_facturar: float,
        url_maps: str | None,
    ) -> TablaKm:
        model = TablaKmModel(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            spst_id=spst_id,
            empresa_nombre=empresa_nombre,
            sucursal_nombre=sucursal_nombre,
            observaciones=observaciones,
            domicilio_cliente=domicilio_cliente,
            localidad_cliente=localidad_cliente,
            provincia_cliente=provincia_cliente,
            kms_recorrido=kms_recorrido,
            umbral_viatico=umbral_viatico,
            aplica_viatico=aplica_viatico,
            kms_a_facturar=kms_a_facturar,
            url_maps=url_maps,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)


def _to_entity(row: TablaKmModel) -> TablaKm:
    return TablaKm(
        id=row.id,
        prestador_id=row.prestador_id,
        spst_id=row.spst_id,
        empresa_nombre=row.empresa_nombre,
        sucursal_nombre=row.sucursal_nombre,
        observaciones=row.observaciones,
        domicilio_cliente=row.domicilio_cliente,
        localidad_cliente=row.localidad_cliente,
        provincia_cliente=row.provincia_cliente,
        kms_recorrido=row.kms_recorrido,
        umbral_viatico=row.umbral_viatico,
        aplica_viatico=row.aplica_viatico,
        kms_a_facturar=row.kms_a_facturar,
        url_maps=row.url_maps,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
