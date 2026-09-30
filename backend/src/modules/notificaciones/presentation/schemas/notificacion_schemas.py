import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.notificaciones.domain.entities.notificacion import Notificacion


class NotificacionOut(BaseModel):
    id: uuid.UUID
    titulo: str
    cuerpo: str
    url: str | None
    creada_en: datetime
    leida: bool

    @classmethod
    def from_entity(cls, n: Notificacion) -> "NotificacionOut":
        return cls(
            id=n.id,
            titulo=n.titulo,
            cuerpo=n.cuerpo,
            url=n.url,
            creada_en=n.creada_en,
            leida=n.leida,
        )


class MarcarLeidasIn(BaseModel):
    """`ids` omitido o null = marcar todas las visibles."""

    ids: list[uuid.UUID] | None = Field(default=None, max_length=500)


class MarcarLeidasOut(BaseModel):
    actualizadas: int
