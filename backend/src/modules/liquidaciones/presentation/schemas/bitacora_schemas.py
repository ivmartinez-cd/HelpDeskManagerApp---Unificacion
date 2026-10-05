"""Schema de `GET /liquidaciones/{id}/bitacora`."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.domain.repositories.bitacora_gateway import EntradaBitacora


class EntradaBitacoraOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    # Hora local de Siges (Argentina), sin zona: el navegador la toma como local.
    fecha: datetime
    usuario: str
    autor: str | None
    es_canal: bool = Field(serialization_alias="esCanal")
    texto: str

    @classmethod
    def from_entity(cls, e: EntradaBitacora) -> "EntradaBitacoraOut":
        return cls(
            id=e.id_consulta,
            fecha=e.fecha,
            usuario=e.usuario,
            autor=e.autor,
            es_canal=e.es_canal,
            texto=e.texto,
        )
