from pydantic import BaseModel, ConfigDict


class CalendarEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    start: str
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


class GetCalendarEventsResponse(BaseModel):
    events: list[CalendarEventSchema]
    total: int
