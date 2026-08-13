import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vacaciones.application.use_cases.actualizar_config import (
    ActualizarConfigCommand,
)
from src.modules.vacaciones.application.use_cases.gestionar_exclusiones import (
    ExclusionConNombresDTO,
)
from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones
from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier


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
    min_advance_notice_days: int = Field(serialization_alias="minAdvanceNoticeDays")
    max_overlap_percent: int = Field(serialization_alias="maxOverlapPercent")
    max_overlap_count: int = Field(serialization_alias="maxOverlapCount")

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
            min_advance_notice_days=config.min_advance_notice_days,
            max_overlap_percent=config.max_overlap_percent,
            max_overlap_count=config.max_overlap_count,
        )


class SeniorityTierRequest(BaseModel):
    """Validación del PUT legacy (zod): min/max >= 0, days 1..365."""

    model_config = ConfigDict(populate_by_name=True)

    min_years: float = Field(alias="minYears", ge=0)
    max_years: float = Field(alias="maxYears", ge=0)
    days: int = Field(ge=1, le=365)


class ConfigUpdateRequest(BaseModel):
    """PUT parcial (paridad legacy): los campos ausentes no se tocan."""

    model_config = ConfigDict(populate_by_name=True)

    seniority_tiers: list[SeniorityTierRequest] | None = Field(
        default=None, alias="seniorityTiers", min_length=1
    )
    min_advance_notice_days: int | None = Field(
        default=None, alias="minAdvanceNoticeDays", ge=0, le=365
    )
    max_overlap_percent: int | None = Field(
        default=None, alias="maxOverlapPercent", ge=0, le=100
    )
    max_overlap_count: int | None = Field(default=None, alias="maxOverlapCount", ge=0)
    next_year_open_month: int | None = Field(
        default=None, alias="nextYearOpenMonth", ge=1, le=12
    )
    next_year_open_day: int | None = Field(
        default=None, alias="nextYearOpenDay", ge=1, le=31
    )
    allow_advance_request: bool | None = Field(default=None, alias="allowAdvanceRequest")
    max_advance_days: int | None = Field(default=None, alias="maxAdvanceDays", ge=0)
    allow_carry_over: bool | None = Field(default=None, alias="allowCarryOver")
    max_carry_over_days: int | None = Field(default=None, alias="maxCarryOverDays", ge=0)

    def to_command(self) -> ActualizarConfigCommand:
        tiers = (
            tuple(
                SeniorityTier(min_years=t.min_years, max_years=t.max_years, days=t.days)
                for t in self.seniority_tiers
            )
            if self.seniority_tiers is not None
            else None
        )
        return ActualizarConfigCommand(
            seniority_tiers=tiers,
            min_advance_notice_days=self.min_advance_notice_days,
            max_overlap_percent=self.max_overlap_percent,
            max_overlap_count=self.max_overlap_count,
            next_year_open_month=self.next_year_open_month,
            next_year_open_day=self.next_year_open_day,
            allow_advance_request=self.allow_advance_request,
            max_advance_days=self.max_advance_days,
            allow_carry_over=self.allow_carry_over,
            max_carry_over_days=self.max_carry_over_days,
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
