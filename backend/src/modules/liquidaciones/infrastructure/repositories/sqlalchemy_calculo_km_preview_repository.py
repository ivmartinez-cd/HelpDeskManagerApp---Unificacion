"""Implementación Postgres del puerto CalculoKmPreviewRepository.

`create` borra los previews anteriores del prestador: solo la última propuesta
es aplicable — evita aplicar un diff que el usuario ya no está viendo."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.calculo_km_preview import (
    CalculoKmPreview,
    PreviewFila,
)
from src.modules.liquidaciones.infrastructure.models.geolocalizacion_models import (
    CalculoKmPreviewModel,
)


class SqlAlchemyCalculoKmPreviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        prestador_id: UUID,
        filas: tuple[PreviewFila, ...],
        sin_ubicar: int,
        sin_ruta: int,
        elementos_google: int,
    ) -> CalculoKmPreview:
        await self._session.execute(
            delete(CalculoKmPreviewModel).where(
                CalculoKmPreviewModel.prestador_id == prestador_id
            )
        )
        model = CalculoKmPreviewModel(
            prestador_id=prestador_id,
            filas=[_fila_to_dict(f) for f in filas],
            sin_ubicar=sin_ubicar,
            sin_ruta=sin_ruta,
            elementos_google=elementos_google,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, preview_id: UUID) -> CalculoKmPreview | None:
        stmt = select(CalculoKmPreviewModel).where(CalculoKmPreviewModel.id == preview_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def delete(self, preview_id: UUID) -> bool:
        row = await self._session.get(CalculoKmPreviewModel, preview_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


def _fila_to_dict(f: PreviewFila) -> dict[str, Any]:
    return {
        "accion": f.accion,
        "tabla_km_id": str(f.tabla_km_id) if f.tabla_km_id else None,
        "siges_sucursal_id": f.siges_sucursal_id,
        "empresa_nombre": f.empresa_nombre,
        "sucursal_nombre": f.sucursal_nombre,
        "domicilio": f.domicilio,
        "localidad": f.localidad,
        "provincia": f.provincia,
        "coords_origen": f.coords_origen,
        "latitud_destino": f.latitud_destino,
        "longitud_destino": f.longitud_destino,
        "latitud_base": f.latitud_base,
        "longitud_base": f.longitud_base,
        "kms_ida": f.kms_ida,
        "kms_vuelta": f.kms_vuelta,
        "kms_total": f.kms_total,
        "umbral_viatico": f.umbral_viatico,
        "aplica_viatico": f.aplica_viatico,
        "kms_a_facturar": f.kms_a_facturar,
        "kms_recorrido_actual": f.kms_recorrido_actual,
        "kms_a_facturar_actual": f.kms_a_facturar_actual,
    }


def _fila_from_dict(d: dict[str, Any]) -> PreviewFila:
    return PreviewFila(
        accion=d["accion"],
        tabla_km_id=UUID(d["tabla_km_id"]) if d.get("tabla_km_id") else None,
        siges_sucursal_id=d.get("siges_sucursal_id"),
        empresa_nombre=d["empresa_nombre"],
        sucursal_nombre=d["sucursal_nombre"],
        domicilio=d.get("domicilio"),
        localidad=d.get("localidad"),
        provincia=d.get("provincia"),
        coords_origen=d["coords_origen"],
        latitud_destino=d["latitud_destino"],
        longitud_destino=d["longitud_destino"],
        latitud_base=d.get("latitud_base", 0.0),
        longitud_base=d.get("longitud_base", 0.0),
        kms_ida=d["kms_ida"],
        kms_vuelta=d["kms_vuelta"],
        kms_total=d["kms_total"],
        umbral_viatico=d["umbral_viatico"],
        aplica_viatico=d["aplica_viatico"],
        kms_a_facturar=d["kms_a_facturar"],
        kms_recorrido_actual=d.get("kms_recorrido_actual"),
        kms_a_facturar_actual=d.get("kms_a_facturar_actual"),
    )


def _to_entity(row: CalculoKmPreviewModel) -> CalculoKmPreview:
    return CalculoKmPreview(
        id=row.id,
        prestador_id=row.prestador_id,
        filas=tuple(_fila_from_dict(d) for d in row.filas),
        sin_ubicar=row.sin_ubicar,
        sin_ruta=row.sin_ruta,
        elementos_google=row.elementos_google,
        created_at=row.created_at,
    )
