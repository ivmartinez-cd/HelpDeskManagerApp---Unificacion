from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.modules.contadores.application.dtos.cliente_nuevo_dtos import (
    CandidatosClientesNuevosResult,
    ClienteNuevoResult,
)
from src.modules.contadores.domain.entities.cliente_nuevo import (
    CandidatoClienteNuevo,
    ResumenSigesClienteNuevo,
)

EstadoClienteNuevo = Literal["ESPERANDO_INSTALACION", "STC_PENDIENTE", "STC_ENVIADO", "CERRADO"]


class ClienteNuevoIn(BaseModel):
    """Payload de alta/edición (snake_case, sin alias — igual que el resto de
    contadores)."""

    cliente: str = Field(..., min_length=1, max_length=200)
    siges_empresa_id: int | None = Field(None, ge=1)
    contrato_nro: str | None = Field(None, max_length=100)
    fecha_firma: date | None = None
    vendedor: str | None = Field(None, max_length=100)
    operador_id: str | None = Field(None, max_length=100)
    implementacion_servicio: str | None = Field(None, max_length=50)
    fecha_estimada_implementacion: date | None = None
    fecha_estimada_primera_facturacion: date | None = None
    dia_corte: int | None = Field(None, ge=1, le=31)
    equipos_previstos: int | None = Field(None, ge=0)
    estado: EstadoClienteNuevo = "ESPERANDO_INSTALACION"
    stc_enviado_el: date | None = None
    notas: str | None = Field(None, max_length=1000)


class ResumenSigesSchema(BaseModel):
    empresa_id: int
    equipos_instalados: int
    instalas: int
    primera_instalacion: date | None
    ultima_instalacion: date | None
    equipos_con_toma: int
    contrato_nro: str | None
    fecha_firma: date | None
    vendedor: str | None
    rubro: str

    @classmethod
    def from_entity(cls, r: ResumenSigesClienteNuevo) -> ResumenSigesSchema:
        return cls(
            empresa_id=r.empresa_id,
            equipos_instalados=r.equipos_instalados,
            instalas=r.instalas,
            primera_instalacion=r.primera_instalacion,
            ultima_instalacion=r.ultima_instalacion,
            equipos_con_toma=r.equipos_con_toma,
            contrato_nro=r.contrato_nro,
            fecha_firma=r.fecha_firma,
            vendedor=r.vendedor,
            rubro=r.rubro,
        )


class ClienteNuevoOut(BaseModel):
    id: uuid.UUID
    cliente: str
    siges_empresa_id: int | None
    contrato_nro: str | None
    fecha_firma: date | None
    vendedor: str | None
    operador_id: str | None
    implementacion_servicio: str | None
    fecha_estimada_implementacion: date | None
    fecha_estimada_primera_facturacion: date | None
    dia_corte: int | None
    equipos_previstos: int | None
    estado: str
    stc_enviado_el: date | None
    notas: str | None
    created_at: datetime
    updated_at: datetime
    siges: ResumenSigesSchema | None
    listo_para_stc: bool

    @classmethod
    def from_result(cls, r: ClienteNuevoResult) -> ClienteNuevoOut:
        return cls(
            id=r.id,
            cliente=r.cliente,
            siges_empresa_id=r.siges_empresa_id,
            contrato_nro=r.contrato_nro,
            fecha_firma=r.fecha_firma,
            vendedor=r.vendedor,
            operador_id=r.operador_id,
            implementacion_servicio=r.implementacion_servicio,
            fecha_estimada_implementacion=r.fecha_estimada_implementacion,
            fecha_estimada_primera_facturacion=r.fecha_estimada_primera_facturacion,
            dia_corte=r.dia_corte,
            equipos_previstos=r.equipos_previstos,
            estado=r.estado,
            stc_enviado_el=r.stc_enviado_el,
            notas=r.notas,
            created_at=r.created_at,
            updated_at=r.updated_at,
            siges=ResumenSigesSchema.from_entity(r.siges) if r.siges else None,
            listo_para_stc=r.listo_para_stc,
        )


class CandidatoClienteNuevoSchema(BaseModel):
    empresa_id: int
    cliente: str
    contrato_nro: str | None
    fecha_firma: date | None
    vendedor: str | None
    rubro: str
    equipos_instalados: int

    @classmethod
    def from_entity(cls, c: CandidatoClienteNuevo) -> CandidatoClienteNuevoSchema:
        return cls(
            empresa_id=c.empresa_id,
            cliente=c.cliente,
            contrato_nro=c.contrato_nro,
            fecha_firma=c.fecha_firma,
            vendedor=c.vendedor,
            rubro=c.rubro,
            equipos_instalados=c.equipos_instalados,
        )


class CandidatosClientesNuevosResponse(BaseModel):
    candidatos: list[CandidatoClienteNuevoSchema]
    firmado_desde: date

    @classmethod
    def from_result(cls, r: CandidatosClientesNuevosResult) -> CandidatosClientesNuevosResponse:
        return cls(
            candidatos=[CandidatoClienteNuevoSchema.from_entity(c) for c in r.candidatos],
            firmado_desde=r.firmado_desde,
        )
