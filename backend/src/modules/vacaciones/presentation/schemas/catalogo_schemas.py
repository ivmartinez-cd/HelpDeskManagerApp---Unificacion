import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vacaciones.application.dtos.gestion_dtos import (
    CargoCommand,
    CargoDTO,
    FeriadoCommand,
    ImportFeriadosResultDTO,
    SectorCommand,
    SectorDTO,
)
from src.modules.vacaciones.domain.entities.feriado import Feriado
from src.modules.vacaciones.domain.repositories.user_directory import UserInfo


class JefeSectorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    email: str
    full_name: str = Field(serialization_alias="fullName")

    @classmethod
    def from_info(cls, info: UserInfo) -> "JefeSectorResponse":
        return cls(id=info.id, email=info.email, full_name=info.full_name)


class SectorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    name: str
    color: str
    empleados_count: int = Field(serialization_alias="empleadosCount")
    jefes: list[JefeSectorResponse]

    @classmethod
    def from_dto(cls, dto: SectorDTO) -> "SectorResponse":
        return cls(
            id=dto.sector.id,
            name=dto.sector.name,
            color=dto.sector.color,
            empleados_count=dto.empleados_count,
            jefes=[JefeSectorResponse.from_info(j) for j in dto.jefes],
        )


class SectorRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#3b82f6", max_length=20)
    jefe_user_id: uuid.UUID | None = Field(default=None, alias="jefeUserId")

    def to_command(self) -> SectorCommand:
        return SectorCommand(name=self.name, color=self.color, jefe_user_id=self.jefe_user_id)


class CargoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    name: str
    max_simultaneos: int | None = Field(serialization_alias="maxSimultaneos")
    empleados_count: int = Field(serialization_alias="empleadosCount")

    @classmethod
    def from_dto(cls, dto: CargoDTO) -> "CargoResponse":
        return cls(
            id=dto.cargo.id,
            name=dto.cargo.name,
            max_simultaneos=dto.cargo.max_simultaneos,
            empleados_count=dto.empleados_count,
        )


class CargoRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    max_simultaneos: int | None = Field(default=None, alias="maxSimultaneos", ge=1)

    def to_command(self) -> CargoCommand:
        return CargoCommand(name=self.name, max_simultaneos=self.max_simultaneos)


class FeriadoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    name: str
    date: date
    deducts_vacation: bool = Field(serialization_alias="deductsVacation")

    @classmethod
    def from_entity(cls, feriado: Feriado) -> "FeriadoResponse":
        return cls(
            id=feriado.id,
            name=feriado.name,
            date=feriado.date,
            deducts_vacation=feriado.deducts_vacation,
        )


class FeriadoRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=200)
    date: date
    deducts_vacation: bool = Field(default=False, alias="deductsVacation")

    def to_command(self) -> FeriadoCommand:
        return FeriadoCommand(
            name=self.name, fecha=self.date, deducts_vacation=self.deducts_vacation
        )


class ImportFeriadosResponse(BaseModel):
    year: int
    count: int
    message: str

    @classmethod
    def from_dto(cls, dto: ImportFeriadosResultDTO) -> "ImportFeriadosResponse":
        return cls(
            year=dto.year,
            count=dto.count,
            message=f"Se importaron {dto.count} feriados del año {dto.year}",
        )
