import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vacaciones.application.use_cases.gestionar_exclusiones import (
    ExclusionConNombresDTO,
)
from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones


class SeniorityTierResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    min_years: float = Field(serialization_alias="minYears")
    max_years: float = Field(serialization_alias="maxYears")
    days: int


class ConfigResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    seniority_tiers: list[SeniorityTierResponse] = Field(serialization_alias="seniorityTiers")
    next_year_open_month: int = Field(serialization_alias="nextYearOpenMonth")
    next_year_open_day: int = Field(serialization_alias="nextYearOpenDay")
    allow_advance_request: bool = Field(serialization_alias="allowAdvanceRequest")
    max_advance_days: int = Field(serialization_alias="maxAdvanceDays")
    allow_carry_over: bool = Field(serialization_alias="allowCarryOver")
    max_carry_over_days: int = Field(serialization_alias="maxCarryOverDays")

    @classmethod
    def from_config(cls, config: ConfigVacaciones) -> "ConfigResponse":
        return cls(
            seniority_tiers=[
                SeniorityTierResponse(
                    min_years=t.min_years, max_years=t.max_years, days=t.days
                )
                for t in config.seniority_tiers
            ],
            next_year_open_month=config.next_year_open_month,
            next_year_open_day=config.next_year_open_day,
            allow_advance_request=config.allow_advance_request,
            max_advance_days=config.max_advance_days,
            allow_carry_over=config.allow_carry_over,
            max_carry_over_days=config.max_carry_over_days,
        )


class ExclusionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    empleado_a_id: uuid.UUID = Field(serialization_alias="empleadoAId")
    empleado_b_id: uuid.UUID = Field(serialization_alias="empleadoBId")
    empleado_a_nombre: str = Field(serialization_alias="empleadoANombre")
    empleado_b_nombre: str = Field(serialization_alias="empleadoBNombre")

    @classmethod
    def from_dto(cls, dto: ExclusionConNombresDTO) -> "ExclusionResponse":
        return cls(
            id=dto.exclusion.id,
            empleado_a_id=dto.exclusion.empleado_a_id,
            empleado_b_id=dto.exclusion.empleado_b_id,
            empleado_a_nombre=dto.empleado_a_nombre,
            empleado_b_nombre=dto.empleado_b_nombre,
        )


class ExclusionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    empleado_a_id: uuid.UUID = Field(alias="empleadoAId")
    empleado_b_id: uuid.UUID = Field(alias="empleadoBId")
