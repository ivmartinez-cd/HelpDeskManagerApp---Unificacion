"""Schemas del cálculo de distancias PST↔sucursal (two-step preview→apply)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.calcular_distancias_siges import (
    AplicarDistanciasResultado,
)
from src.modules.liquidaciones.domain.entities.calculo_km_preview import (
    CalculoKmPreview,
    PreviewFila,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalPropia,
)


class SucursalPropiaOut(BaseModel):
    """Sucursal propia del PST — para el dropdown de selección de base."""

    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    descripcion: str
    latitud: str | None
    longitud: str | None
    tiene_coords: bool = Field(serialization_alias="tieneCoords")

    @classmethod
    def from_entity(cls, e: SigesSucursalPropia) -> SucursalPropiaOut:
        return cls(
            siges_sucursal_id=e.siges_sucursal_id,
            descripcion=e.descripcion,
            latitud=e.latitud,
            longitud=e.longitud,
            tiene_coords=e.latitud is not None and e.longitud is not None,
        )


class PreviewFilaOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    accion: str
    tabla_km_id: uuid.UUID | None = Field(serialization_alias="tablaKmId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    coords_origen: str = Field(serialization_alias="coordsOrigen")
    latitud_destino: float = Field(serialization_alias="latitudDestino")
    longitud_destino: float = Field(serialization_alias="longitudDestino")
    kms_ida: float = Field(serialization_alias="kmsIda")
    kms_vuelta: float = Field(serialization_alias="kmsVuelta")
    kms_total: float = Field(serialization_alias="kmsTotal")
    umbral_viatico: float = Field(serialization_alias="umbralViatico")
    aplica_viatico: bool = Field(serialization_alias="aplicaViatico")
    kms_a_facturar: float = Field(serialization_alias="kmsAFacturar")
    kms_recorrido_actual: float | None = Field(serialization_alias="kmsRecorridoActual")
    kms_a_facturar_actual: float | None = Field(serialization_alias="kmsAFacturarActual")

    @classmethod
    def from_entity(cls, f: PreviewFila) -> PreviewFilaOut:
        return cls(
            accion=f.accion,
            tabla_km_id=f.tabla_km_id,
            empresa_nombre=f.empresa_nombre,
            sucursal_nombre=f.sucursal_nombre,
            coords_origen=f.coords_origen,
            latitud_destino=f.latitud_destino,
            longitud_destino=f.longitud_destino,
            kms_ida=f.kms_ida,
            kms_vuelta=f.kms_vuelta,
            kms_total=f.kms_total,
            umbral_viatico=f.umbral_viatico,
            aplica_viatico=f.aplica_viatico,
            kms_a_facturar=f.kms_a_facturar,
            kms_recorrido_actual=f.kms_recorrido_actual,
            kms_a_facturar_actual=f.kms_a_facturar_actual,
        )


class CalculoKmPreviewOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    filas: list[PreviewFilaOut]
    sin_ubicar: int = Field(serialization_alias="sinUbicar")
    sin_ruta: int = Field(serialization_alias="sinRuta")
    elementos_google: int = Field(serialization_alias="elementosGoogle")
    sin_actividad: int = Field(serialization_alias="sinActividad")
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_entity(cls, p: CalculoKmPreview) -> CalculoKmPreviewOut:
        return cls(
            id=p.id,
            prestador_id=p.prestador_id,
            filas=[PreviewFilaOut.from_entity(f) for f in p.filas],
            sin_ubicar=p.sin_ubicar,
            sin_ruta=p.sin_ruta,
            elementos_google=p.elementos_google,
            sin_actividad=p.sin_actividad,
            created_at=p.created_at,
        )


class AplicarDistanciasIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    preview_id: uuid.UUID = Field(alias="previewId")


class AplicarDistanciasOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    creadas: int
    actualizadas: int

    @classmethod
    def from_resultado(cls, r: AplicarDistanciasResultado) -> AplicarDistanciasOut:
        return cls(creadas=r.creadas, actualizadas=r.actualizadas)
