"""Implementación Postgres del puerto TablaKmRepository (tabla tabla_kms)."""

import uuid
from datetime import UTC, datetime
from typing import Any
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
        # id como desempate: empresa+sucursal pueden repetirse y sin orden total
        # la paginación Page[T] puede repetir/saltear filas entre páginas.
        stmt = select(TablaKmModel).order_by(
            TablaKmModel.empresa_nombre, TablaKmModel.sucursal_nombre, TablaKmModel.id
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
        latitud_destino: float | None = None,
        longitud_destino: float | None = None,
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
        row.latitud_destino = latitud_destino
        row.longitud_destino = longitud_destino
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def set_coordenadas(
        self,
        tabla_km_id: UUID,
        *,
        latitud: float,
        longitud: float,
        coords_origen: str,
        geocode_formatted_address: str | None,
        geocode_fecha: datetime | None,
    ) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if row is None:
            return None
        row.latitud_destino = latitud
        row.longitud_destino = longitud
        row.coords_origen = coords_origen
        row.geocode_formatted_address = geocode_formatted_address
        row.geocode_fecha = geocode_fecha
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def update_distancias(
        self,
        tabla_km_id: UUID,
        *,
        kms_ida: float,
        kms_vuelta: float,
        kms_recorrido: float,
        aplica_viatico: bool,
        kms_a_facturar: float,
        url_maps: str | None,
        latitud_destino: float,
        longitud_destino: float,
        coords_origen: str,
        siges_sucursal_id: int | None = None,
        id_costo_servicios: int | None = None,
    ) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if row is None:
            return None
        row.kms_ida = kms_ida
        row.kms_vuelta = kms_vuelta
        row.kms_recorrido = kms_recorrido
        row.aplica_viatico = aplica_viatico
        row.kms_a_facturar = kms_a_facturar
        row.url_maps = url_maps
        row.latitud_destino = latitud_destino
        row.longitud_destino = longitud_destino
        row.coords_origen = coords_origen
        if siges_sucursal_id is not None:
            row.siges_sucursal_id = siges_sucursal_id
        if id_costo_servicios is not None:
            row.id_costo_servicios = id_costo_servicios
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def update_vinculo_spst(
        self, tabla_km_id: UUID, *, spst_id: UUID | None
    ) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if row is None:
            return None
        row.spst_id = spst_id
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def update_vinculo_siges(
        self,
        tabla_km_id: UUID,
        *,
        siges_sucursal_id: int,
        id_costo_servicios: int | None,
    ) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if row is None:
            return None
        row.siges_sucursal_id = siges_sucursal_id
        row.id_costo_servicios = id_costo_servicios
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def update_domicilio(
        self,
        tabla_km_id: UUID,
        *,
        domicilio_cliente: str | None,
        localidad_cliente: str | None,
        provincia_cliente: str | None,
        siges_sucursal_id: int | None = None,
        id_costo_servicios: int | None = None,
    ) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if row is None:
            return None
        row.domicilio_cliente = domicilio_cliente
        row.localidad_cliente = localidad_cliente
        row.provincia_cliente = provincia_cliente
        row.geocode_formatted_address = None
        row.geocode_fecha = None
        if siges_sucursal_id is not None:
            row.siges_sucursal_id = siges_sucursal_id
        if id_costo_servicios is not None:
            row.id_costo_servicios = id_costo_servicios
        row.updated_at = datetime.now(UTC)
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

    async def create(self, **campos: Any) -> TablaKm:
        """La firma tipada (keyword-only, una por columna) vive en el puerto
        `TablaKmRepository`; repetirla acá solo duplicaba la lista de columnas
        — mismo criterio que el fake del puerto."""
        model = TablaKmModel(id=uuid.uuid4(), **campos)
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
        latitud_destino=row.latitud_destino,
        longitud_destino=row.longitud_destino,
        created_at=row.created_at,
        updated_at=row.updated_at,
        kms_ida=row.kms_ida,
        kms_vuelta=row.kms_vuelta,
        coords_origen=row.coords_origen,
        geocode_formatted_address=row.geocode_formatted_address,
        geocode_fecha=row.geocode_fecha,
        siges_sucursal_id=row.siges_sucursal_id,
        id_costo_servicios=row.id_costo_servicios,
    )
