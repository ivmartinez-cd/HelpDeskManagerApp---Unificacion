import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.personas.domain.entities.persona import AccesoPersona, DatosPersona, Persona


class AccesoResponse(BaseModel):
    user_id: uuid.UUID = Field(serialization_alias="userId")
    activo: bool
    superadmin: bool
    ultimo_ingreso: datetime | None = Field(serialization_alias="ultimoIngreso")

    @classmethod
    def from_entity(cls, acceso: AccesoPersona) -> "AccesoResponse":
        return cls(
            user_id=acceso.user_id,
            activo=acceso.activo,
            superadmin=acceso.superadmin,
            ultimo_ingreso=acceso.ultimo_ingreso,
        )


class PersonaResponse(BaseModel):
    id: uuid.UUID
    first_name: str = Field(serialization_alias="firstName")
    last_name: str = Field(serialization_alias="lastName")
    email: str
    color: str
    activa: bool
    sector_id: uuid.UUID = Field(serialization_alias="sectorId")
    sector_nombre: str = Field(serialization_alias="sectorNombre")
    cargo_nombre: str = Field(serialization_alias="cargoNombre")
    entra_a_la_app: bool = Field(serialization_alias="entraALaApp")
    acceso: AccesoResponse | None

    @classmethod
    def from_entity(cls, persona: Persona) -> "PersonaResponse":
        return cls(
            id=persona.id,
            first_name=persona.datos.first_name,
            last_name=persona.datos.last_name,
            email=persona.datos.email,
            color=persona.datos.color,
            activa=persona.activa,
            sector_id=persona.sector_id,
            sector_nombre=persona.sector_nombre,
            cargo_nombre=persona.cargo_nombre,
            entra_a_la_app=persona.entra_a_la_app,
            acceso=AccesoResponse.from_entity(persona.acceso) if persona.acceso else None,
        )


class DatosPersonaRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    first_name: str = Field(alias="firstName", min_length=1, max_length=100)
    last_name: str = Field(alias="lastName", min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    color: str = Field(max_length=20)

    def to_datos(self) -> DatosPersona:
        return DatosPersona(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            color=self.color,
        )
