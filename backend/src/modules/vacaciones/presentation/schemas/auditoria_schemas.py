import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vacaciones.application.use_cases.listar_auditoria import (
    RegistroAuditoriaDTO,
)


class RegistroAuditoriaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    accion: str
    entidad: str
    entidad_id: str | None = Field(serialization_alias="entidadId")
    usuario_email: str | None = Field(serialization_alias="usuarioEmail")
    metadata: dict[str, object]
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_dto(cls, dto: RegistroAuditoriaDTO) -> "RegistroAuditoriaResponse":
        r = dto.registro
        return cls(
            id=r.id,
            accion=r.accion,
            entidad=r.entidad,
            entidad_id=r.entidad_id,
            usuario_email=dto.user_email,
            metadata=r.metadata,
            created_at=r.created_at,
        )
