import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.modules.vacaciones.application.dtos.ausencia_dtos import (
    AusenciaDTO,
    CrearAusenciaCommand,
    DescuentoRowDTO,
    EditarAusenciaCommand,
)
from src.modules.vacaciones.domain.entities.ausencia import TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud


class AusenciaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    empleado_id: uuid.UUID = Field(serialization_alias="empleadoId")
    empleado_nombre: str = Field(serialization_alias="empleadoNombre")
    empleado_color: str = Field(serialization_alias="empleadoColor")
    sector_nombre: str = Field(serialization_alias="sectorNombre")
    sector_color: str = Field(serialization_alias="sectorColor")
    start_date: date = Field(serialization_alias="startDate")
    end_date: date = Field(serialization_alias="endDate")
    days_count: int = Field(serialization_alias="daysCount")
    half_day: bool = Field(serialization_alias="halfDay")
    tipo: str
    reason: str | None
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_dto(cls, dto: AusenciaDTO) -> "AusenciaResponse":
        a = dto.ausencia
        return cls(
            id=a.id,
            empleado_id=a.empleado_id,
            empleado_nombre=dto.empleado_nombre,
            empleado_color=dto.empleado_color,
            sector_nombre=dto.sector_nombre,
            sector_color=dto.sector_color,
            start_date=a.start_date,
            end_date=a.end_date,
            days_count=a.days_count,
            half_day=a.half_day,
            tipo=a.tipo.value,
            reason=a.reason,
            status=a.status.value,
            created_at=a.created_at,
        )


class _RangoAusencia(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    tipo: TipoAusencia
    reason: str | None = Field(default=None, max_length=500)
    half_day: bool = Field(default=False, alias="halfDay")

    @model_validator(mode="after")
    def _rango_valido(self) -> "_RangoAusencia":
        if self.end_date < self.start_date:
            raise ValueError("La fecha de fin debe ser posterior o igual a la de inicio")
        return self


class CrearAusenciaRequest(_RangoAusencia):
    empleado_ids: list[uuid.UUID] = Field(default_factory=list, alias="empleadoIds")

    def to_command(self) -> CrearAusenciaCommand:
        return CrearAusenciaCommand(
            empleado_ids=self.empleado_ids,
            start_date=self.start_date,
            end_date=self.end_date,
            tipo=self.tipo,
            reason=self.reason,
            half_day=self.half_day,
        )


class EditarAusenciaRequest(_RangoAusencia):
    status: EstadoSolicitud | None = None

    def to_command(self) -> EditarAusenciaCommand:
        return EditarAusenciaCommand(
            start_date=self.start_date,
            end_date=self.end_date,
            tipo=self.tipo,
            reason=self.reason,
            half_day=self.half_day,
            status=self.status,
        )


class DescuentoRowResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    empleado_id: uuid.UUID = Field(serialization_alias="empleadoId")
    first_name: str = Field(serialization_alias="firstName")
    last_name: str = Field(serialization_alias="lastName")
    cargo_nombre: str = Field(serialization_alias="cargoNombre")
    dias_descontados: float = Field(serialization_alias="diasDescontados")
    dias_enfermedad: int = Field(serialization_alias="diasEnfermedad")
    guardias: int

    @classmethod
    def from_dto(cls, dto: DescuentoRowDTO) -> "DescuentoRowResponse":
        return cls(
            empleado_id=dto.empleado_id,
            first_name=dto.first_name,
            last_name=dto.last_name,
            cargo_nombre=dto.cargo_nombre,
            dias_descontados=dto.dias_descontados,
            dias_enfermedad=dto.dias_enfermedad,
            guardias=dto.guardias,
        )
