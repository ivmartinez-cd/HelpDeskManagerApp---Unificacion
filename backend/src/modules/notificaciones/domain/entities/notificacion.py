import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NuevaNotificacion:
    """Lo que publica un módulo. `clave` identifica el hecho avisado (p. ej.
    `sla.visita-sucursal:123:456`): publicar dos veces la misma clave no
    duplica — el job que la genera puede correr cada pocos minutos o
    reintentar sin preocuparse. `audiencia`: ver `value_objects/audiencia.py`.
    `url`: ruta interna de la app a la que lleva el click (o None)."""

    clave: str
    audiencia: str
    titulo: str
    cuerpo: str
    url: str | None = None


@dataclass(frozen=True, slots=True)
class Notificacion:
    """Una notificación vista por un usuario concreto: `leida` es de ese
    usuario, no global (cada destinatario la marca por su cuenta)."""

    id: uuid.UUID
    titulo: str
    cuerpo: str
    url: str | None
    creada_en: datetime
    leida: bool
