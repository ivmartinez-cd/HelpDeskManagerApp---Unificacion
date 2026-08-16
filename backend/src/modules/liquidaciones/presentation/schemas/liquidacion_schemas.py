"""Schemas de GET /api/liquidaciones, GET /api/liquidaciones/{id} y
GET /api/liquidaciones/prestadores. Módulo nuevo, sin contrato legacy que preservar —
snake_case en Python, camelCase en el wire (mismo patrón que turnos/sla)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.entities.prestador import Prestador

ESTADOS_VALIDOS = Literal[
    "abierta", "preliquidada", "recibida", "observada", "aprobada", "cerrada"
]


class PorEstadoPendientesOut(BaseModel):
    abierta: int = 0
    preliquidada: int = 0
    recibida: int = 0
    observada: int = 0


class ResumenLiquidacionesOut(BaseModel):
    pendientes: int
    por_estado: PorEstadoPendientesOut = Field(serialization_alias="porEstado")


class EstadoIn(BaseModel):
    estado: ESTADOS_VALIDOS


class ExtraIn(BaseModel):
    concepto_extra: str | None = Field(None, alias="conceptoExtra")
    monto_extra: float | None = Field(None, alias="montoExtra")

    model_config = ConfigDict(populate_by_name=True)


class PrestadorLiquidacionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    nombre: str
    nombre_corto: str = Field(serialization_alias="nombreCorto")
    cuit: str | None
    region: str | None
    activo: bool
    siges_empresa_id: int | None = Field(default=None, serialization_alias="sigesEmpresaId")
    cd_prestador_id: int | None = Field(default=None, serialization_alias="cdPrestadorId")
    siges_base_sucursal_id: int | None = Field(
        default=None, serialization_alias="sigesBaseSucursalId"
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_entity(cls, e: Prestador) -> "PrestadorLiquidacionOut":
        return cls(
            id=e.id,
            nombre=e.nombre,
            nombre_corto=e.nombre_corto,
            cuit=e.cuit,
            region=e.region,
            activo=e.activo,
            siges_empresa_id=e.siges_empresa_id,
            cd_prestador_id=e.cd_prestador_id,
            siges_base_sucursal_id=e.siges_base_sucursal_id,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )


class LiquidacionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    numero_liquidacion: str | None = Field(serialization_alias="numeroLiquidacion")
    periodo: str
    tipo_liquidacion: str = Field(serialization_alias="tipoLiquidacion")
    nombre_archivo: str | None = Field(serialization_alias="nombreArchivo")
    fecha_importacion: datetime = Field(serialization_alias="fechaImportacion")
    estado: str
    total_incidentes: int = Field(serialization_alias="totalIncidentes")
    total_alertas: int = Field(serialization_alias="totalAlertas")
    total_importe: float = Field(serialization_alias="totalImporte")
    concepto_extra: str | None = Field(None, serialization_alias="conceptoExtra")
    monto_extra: float | None = Field(None, serialization_alias="montoExtra")

    @classmethod
    def from_entity(cls, e: Liquidacion) -> "LiquidacionOut":
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            numero_liquidacion=e.numero_liquidacion,
            periodo=e.periodo,
            tipo_liquidacion=e.tipo_liquidacion,
            nombre_archivo=e.nombre_archivo,
            fecha_importacion=e.fecha_importacion,
            estado=e.estado,
            total_incidentes=e.total_incidentes,
            total_alertas=e.total_alertas,
            total_importe=e.total_importe,
            concepto_extra=e.concepto_extra,
            monto_extra=e.monto_extra,
        )
