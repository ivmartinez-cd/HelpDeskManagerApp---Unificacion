"""Acción que un operador registra sobre un envío desde "Registrar acción" (tabla
`insumos_despacho_accion`). Solo se agregan: no se editan ni se borran."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class TipoAccion(StrEnum):
    LLAMADO_CLIENTE = "llamado_cliente"
    MAIL_CLIENTE = "mail_cliente"
    RECLAMO_OCA = "reclamo_oca"
    OTRO = "otro"


class ResultadoAccion(StrEnum):
    RESUELTO = "resuelto"
    PENDIENTE = "pendiente"
    SIN_RESPUESTA = "sin_respuesta"


@dataclass(frozen=True, slots=True)
class AccionNueva:
    guia: str
    tipo: TipoAccion
    detalle: str
    resultado: ResultadoAccion
    cerro_alerta: bool
    usuario_id: UUID | None
    usuario_nombre: str


@dataclass(frozen=True, slots=True)
class AccionRegistrada:
    id: int
    guia: str
    tipo: TipoAccion
    detalle: str
    resultado: ResultadoAccion
    cerro_alerta: bool
    usuario_id: UUID | None
    usuario_nombre: str
    creada_en: datetime
