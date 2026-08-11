from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
