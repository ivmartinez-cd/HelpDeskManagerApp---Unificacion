"""Alerta agrupada sobre varios incidentes — observaciones / observacion_incidentes.

A diferencia de `Alerta` (1:1 incidente×regla), una `Observacion` agrupa N incidentes
relacionados vía `ObservacionIncidente` (con `rol` "principal" — el que tiene el error
central — o "referencia"). Hoy solo la genera ALT005 (Ruta Compartida,
`tipo_observacion="RUTA_COMPARTIDA"`), y solo cuando esa regla está activa (desactivada
por default — ver `LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §3/§7).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

SEVERIDAD_INFORMATIVO = "INFORMATIVO"
SEVERIDAD_ADVERTENCIA = "ADVERTENCIA"
SEVERIDAD_CRITICO = "CRITICO"
SEVERIDAD_AJUSTE_SUGERIDO = "AJUSTE_SUGERIDO"

ESTADO_PENDIENTE = "pendiente"
ESTADO_EN_REVISION = "en_revision"
ESTADO_RESUELTA = "resuelta"
ESTADO_RECHAZADA = "rechazada"
ESTADO_EXCEPCION_APROBADA = "excepcion_aprobada"

ROL_PRINCIPAL = "principal"
ROL_REFERENCIA = "referencia"


@dataclass(frozen=True)
class Observacion:
    id: uuid.UUID
    liquidacion_id: uuid.UUID
    tipo_observacion: str
    severidad: str
    titulo: str
    descripcion: str | None
    datos_contexto: dict[str, Any]
    monto_cobrado: float
    monto_esperado: float
    diferencia: float
    estado: str
    regla_codigo: str | None
    fecha_generacion: datetime


@dataclass(frozen=True)
class ObservacionIncidente:
    id: uuid.UUID
    observacion_id: uuid.UUID
    incidente_id: uuid.UUID
    rol: str
