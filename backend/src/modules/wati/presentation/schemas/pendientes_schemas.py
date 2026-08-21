from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversacionPendienteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    wa_id: str
    nombre: str
    operador_nombre: str | None
    operador_email: str | None
    sin_asignar: bool
    esperando_desde: datetime
    minutos_esperando: int
    ultimo_mensaje_cliente_at: datetime | None
    ultimo_texto_cliente: str


class OperadorPendientesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operador: str
    cantidad: int


class PendientesResumenResponse(BaseModel):
    total: int
    sin_asignar: int
    max_minutos_esperando: int
    por_operador: list[OperadorPendientesSchema]
    sincronizado_at: datetime | None
    inbox_url: str | None
    """URL del Team Inbox de WATI (config del backend) para linkear desde la UI."""


class SyncResultadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contactos_revisados: int
    esperando: int
    descartados: int
