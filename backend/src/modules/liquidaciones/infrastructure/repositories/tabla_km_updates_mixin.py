"""Mitad "escrituras" de `SqlAlchemyTablaKmRepository`: todos los métodos que
mutan una fila de `tabla_kms`, separados en un mixin para que ninguna de las
dos mitades (esta y la de consultas, en `sqlalchemy_tabla_km_repository.py`)
exceda el límite de tamaño de clase (ARCHITECTURE_GUIDE.md §4)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Update, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.infrastructure.models.tabla_km_model import TablaKmModel
from src.modules.liquidaciones.infrastructure.repositories.tabla_km_cambios import (
    CambiosTablaKm,
    aplicar_cambios,
    vinculo_siges_si_presente,
)
from src.modules.liquidaciones.infrastructure.repositories.tabla_km_row_mapper import to_entity


class _TablaKmUpdatesMixin:
    _session: AsyncSession

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
        # Edición completa desde el ABM; no toca `updated_at` (comportamiento heredado)
        # ni el pin destino (latitud_destino/longitud_destino) — eso lo escriben
        # solo `set_coordenadas`/`update_distancias`. Antes este método incluía esas
        # dos columnas en el dict de cambios con default None, así que CUALQUIER
        # edición desde el ABM las pisaba a NULL aunque el usuario no las tocara.
        cambios = CambiosTablaKm(
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
        return await self._actualizar(tabla_km_id, cambios)

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
        cambios = CambiosTablaKm(
            latitud_destino=latitud,
            longitud_destino=longitud,
            coords_origen=coords_origen,
            geocode_formatted_address=geocode_formatted_address,
            geocode_fecha=geocode_fecha,
            updated_at=datetime.now(UTC),
        )
        return await self._actualizar(tabla_km_id, cambios)

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
        cambios = CambiosTablaKm(
            kms_ida=kms_ida,
            kms_vuelta=kms_vuelta,
            kms_recorrido=kms_recorrido,
            aplica_viatico=aplica_viatico,
            kms_a_facturar=kms_a_facturar,
            url_maps=url_maps,
            latitud_destino=latitud_destino,
            longitud_destino=longitud_destino,
            coords_origen=coords_origen,
            updated_at=datetime.now(UTC),
        )
        cambios.update(vinculo_siges_si_presente(siges_sucursal_id, id_costo_servicios))
        return await self._actualizar(tabla_km_id, cambios)

    async def update_vinculo_spst(
        self, tabla_km_id: UUID, *, spst_id: UUID | None
    ) -> TablaKm | None:
        cambios = CambiosTablaKm(spst_id=spst_id, updated_at=datetime.now(UTC))
        return await self._actualizar(tabla_km_id, cambios)

    async def update_vinculo_siges(
        self,
        tabla_km_id: UUID,
        *,
        siges_sucursal_id: int,
        id_costo_servicios: int | None,
    ) -> TablaKm | None:
        cambios = CambiosTablaKm(
            siges_sucursal_id=siges_sucursal_id,
            id_costo_servicios=id_costo_servicios,
            updated_at=datetime.now(UTC),
        )
        return await self._actualizar(tabla_km_id, cambios)

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
        # Cambió la dirección: el geocode previo deja de valer.
        cambios = CambiosTablaKm(
            domicilio_cliente=domicilio_cliente,
            localidad_cliente=localidad_cliente,
            provincia_cliente=provincia_cliente,
            geocode_formatted_address=None,
            geocode_fecha=None,
            updated_at=datetime.now(UTC),
        )
        cambios.update(vinculo_siges_si_presente(siges_sucursal_id, id_costo_servicios))
        return await self._actualizar(tabla_km_id, cambios)

    async def update_kms_a_facturar(
        self, tabla_km_id: UUID, kms_a_facturar: float
    ) -> TablaKm | None:
        return await _set_campos(self._session, tabla_km_id, kms_a_facturar=kms_a_facturar)

    async def update_archivada(self, tabla_km_id: UUID, archivada: bool) -> TablaKm | None:
        return await _set_campos(self._session, tabla_km_id, archivada=archivada)

    async def set_coordenadas_por_siges_sucursal(
        self,
        prestador_id: UUID,
        siges_sucursal_id: int,
        *,
        latitud: float,
        longitud: float,
        coords_origen: str,
    ) -> int:
        stmt = _stmt_pin_por_siges_sucursal(
            prestador_id,
            siges_sucursal_id,
            latitud=latitud,
            longitud=longitud,
            coords_origen=coords_origen,
        )
        resultado: CursorResult[tuple[()]] = await self._session.execute(stmt)  # type: ignore[assignment]
        await self._session.flush()
        return int(resultado.rowcount or 0)

    async def _actualizar(self, tabla_km_id: UUID, cambios: CambiosTablaKm) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if row is None:
            return None
        aplicar_cambios(row, cambios)
        await self._session.flush()
        await self._session.refresh(row)
        return to_entity(row)


def _stmt_pin_por_siges_sucursal(
    prestador_id: UUID,
    siges_sucursal_id: int,
    *,
    latitud: float,
    longitud: float,
    coords_origen: str,
) -> Update:
    return (
        update(TablaKmModel)
        .where(
            TablaKmModel.prestador_id == prestador_id,
            TablaKmModel.siges_sucursal_id == siges_sucursal_id,
            TablaKmModel.archivada.is_(False),
        )
        .values(
            latitud_destino=latitud, longitud_destino=longitud,
            coords_origen=coords_origen, updated_at=datetime.now(UTC),
        )
    )


async def _set_campos(session: AsyncSession, tabla_km_id: UUID, **campos: object) -> TablaKm | None:
    row = await session.get(TablaKmModel, tabla_km_id)
    if row is None:
        return None
    for campo, valor in campos.items():
        setattr(row, campo, valor)
    await session.flush()
    return to_entity(row)
