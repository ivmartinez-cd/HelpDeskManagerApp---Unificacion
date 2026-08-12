"""Schema de GET /api/liquidaciones/{id} — liquidación + incidentes + alertas +
observaciones en un solo payload (mismo shape que el legacy resolvía con relaciones
ORM perezosas)."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.liquidacion_detalle import LiquidacionDetalle
from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.observacion import Observacion
from src.modules.liquidaciones.presentation.schemas.liquidacion_schemas import LiquidacionOut


class IncidenteOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    numero_incidente: str = Field(serialization_alias="numeroIncidente")
    tipo: str
    empresa_nombre: str | None = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str | None = Field(serialization_alias="sucursalNombre")
    fecha_cierre: date | None = Field(serialization_alias="fechaCierre")
    costo_servicio_cobrado: float = Field(serialization_alias="costoServicioCobrado")
    cant_km_cobrado: float = Field(serialization_alias="cantKmCobrado")
    costo_total_cobrado: float = Field(serialization_alias="costoTotalCobrado")
    costo_servicio_esperado: float | None = Field(serialization_alias="costoServicioEsperado")
    cant_km_esperado: float | None = Field(serialization_alias="cantKmEsperado")
    estado_validacion: str = Field(serialization_alias="estadoValidacion")

    @classmethod
    def from_entity(cls, e: Incidente) -> "IncidenteOut":
        return cls(
            id=e.id,
            numero_incidente=e.numero_incidente,
            tipo=e.tipo,
            empresa_nombre=e.empresa_nombre,
            sucursal_nombre=e.sucursal_nombre,
            fecha_cierre=e.fecha_cierre,
            costo_servicio_cobrado=e.costo_servicio_cobrado,
            cant_km_cobrado=e.cant_km_cobrado,
            costo_total_cobrado=e.costo_total_cobrado,
            costo_servicio_esperado=e.costo_servicio_esperado,
            cant_km_esperado=e.cant_km_esperado,
            estado_validacion=e.estado_validacion,
        )


class AlertaOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    incidente_id: uuid.UUID = Field(serialization_alias="incidenteId")
    tipo_alerta: str = Field(serialization_alias="tipoAlerta")
    descripcion: str | None
    datos_contexto: dict[str, Any] | None = Field(serialization_alias="datosContexto")
    riesgo: float
    estado: str
    fecha_generacion: datetime = Field(serialization_alias="fechaGeneracion")

    @classmethod
    def from_entity(cls, e: Alerta) -> "AlertaOut":
        return cls(
            id=e.id,
            incidente_id=e.incidente_id,
            tipo_alerta=e.tipo_alerta,
            descripcion=e.descripcion,
            datos_contexto=e.datos_contexto,
            riesgo=e.riesgo,
            estado=e.estado,
            fecha_generacion=e.fecha_generacion,
        )


class ObservacionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    tipo_observacion: str = Field(serialization_alias="tipoObservacion")
    severidad: str
    titulo: str
    descripcion: str | None
    monto_cobrado: float = Field(serialization_alias="montoCobrado")
    monto_esperado: float = Field(serialization_alias="montoEsperado")
    diferencia: float
    estado: str
    fecha_generacion: datetime = Field(serialization_alias="fechaGeneracion")

    @classmethod
    def from_entity(cls, e: Observacion) -> "ObservacionOut":
        return cls(
            id=e.id,
            tipo_observacion=e.tipo_observacion,
            severidad=e.severidad,
            titulo=e.titulo,
            descripcion=e.descripcion,
            monto_cobrado=e.monto_cobrado,
            monto_esperado=e.monto_esperado,
            diferencia=e.diferencia,
            estado=e.estado,
            fecha_generacion=e.fecha_generacion,
        )


class LiquidacionDetalleOut(BaseModel):
    liquidacion: LiquidacionOut
    incidentes: list[IncidenteOut]
    alertas: list[AlertaOut]
    observaciones: list[ObservacionOut]

    @classmethod
    def from_dto(cls, dto: LiquidacionDetalle) -> "LiquidacionDetalleOut":
        return cls(
            liquidacion=LiquidacionOut.from_entity(dto.liquidacion),
            incidentes=[IncidenteOut.from_entity(i) for i in dto.incidentes],
            alertas=[AlertaOut.from_entity(a) for a in dto.alertas],
            observaciones=[ObservacionOut.from_entity(o) for o in dto.observaciones],
        )
