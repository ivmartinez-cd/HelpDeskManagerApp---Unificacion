import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from src.modules.contadores.application.dtos.asignacion_override_dto import AsignacionOverrideDTO


class CalendarEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    start: str
    operador_id: str | None = None
    all_day: bool = True
    background_color: str | None = None
    border_color: str | None = None
    type: str | None = None
    tittle_tooltip: str | None = None
    content_tooltip: str | None = None
    string_tipo_evento: str | None = None
    cliente: str | None = None
    vendedor: str | None = None
    fecha_entrega: str | None = None
    fecha_entrega_deseada: str | None = None
    sucursal_entrega: str | None = None
    sucursal_instalacion: str | None = None
    sucursal_despacho: str | None = None
    contacto_entrega: str | None = None
    contacto_instalacion: str | None = None
    bultos: int | float | None = None
    costo_seguro: str | None = None
    costo_recambio: str | None = None


class OperadorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    color: str | None = None


class SyncCalendarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operadores_count: int
    events_count: int
    range_start: str
    range_end: str
    synced_at: datetime


class SyncStatusResponse(BaseModel):
    last_synced_at: datetime | None
    total_events: int


class MiOperadorResponse(BaseModel):
    operador_id: str | None
    nombre: str | None
    color: str | None


class AsignacionOverrideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    operador_ausente_id: str
    operador_ausente_nombre: str | None
    operador_reemplazante_id: str
    operador_reemplazante_nombre: str | None
    vigente_desde: date
    vigente_hasta: date
    alcance_total: bool
    clientes: list[str]
    estado: str
    motivo: str | None

    @classmethod
    def from_dto(cls, dto: AsignacionOverrideDTO) -> "AsignacionOverrideResponse":
        return cls(
            id=dto.id,
            operador_ausente_id=dto.operador_ausente_id,
            operador_ausente_nombre=dto.operador_ausente_nombre,
            operador_reemplazante_id=dto.operador_reemplazante_id,
            operador_reemplazante_nombre=dto.operador_reemplazante_nombre,
            vigente_desde=dto.vigente_desde,
            vigente_hasta=dto.vigente_hasta,
            alcance_total=dto.alcance_total,
            clientes=dto.clientes,
            estado=dto.estado,
            motivo=dto.motivo,
        )


class CreateAsignacionOverrideRequest(BaseModel):
    operador_ausente_id: str
    operador_reemplazante_id: str
    vigente_desde: date
    vigente_hasta: date
    clientes: list[str] | None = None
    motivo: str | None = None
