import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.modules.vacaciones.application.dtos.solicitud_dtos import (
    AfectaTurnosAviso,
    AprobacionDTO,
    CrearSolicitudCommand,
    DecidirSolicitudCommand,
    EditarSolicitudCommand,
    SolapamientosDTO,
    SolicitudDTO,
)
from src.modules.vacaciones.domain.entities.aprobacion import Decision


class AprobacionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    decision: str
    comment: str | None
    created_at: datetime = Field(serialization_alias="createdAt")
    approver_email: str | None = Field(serialization_alias="approverEmail")

    @classmethod
    def from_dto(cls, dto: AprobacionDTO) -> "AprobacionResponse":
        return cls(
            id=dto.aprobacion.id,
            decision=dto.aprobacion.decision.value,
            comment=dto.aprobacion.comment,
            created_at=dto.aprobacion.created_at,
            approver_email=dto.approver_email,
        )


class SolicitudResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    empleado_id: uuid.UUID = Field(serialization_alias="empleadoId")
    empleado_nombre: str = Field(serialization_alias="empleadoNombre")
    empleado_color: str = Field(serialization_alias="empleadoColor")
    sector_nombre: str = Field(serialization_alias="sectorNombre")
    sector_color: str = Field(serialization_alias="sectorColor")
    start_date: date = Field(serialization_alias="startDate")
    end_date: date = Field(serialization_alias="endDate")
    days_requested: int = Field(serialization_alias="daysRequested")
    charged_to_year: int | None = Field(serialization_alias="chargedToYear")
    reason: str | None
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")
    aprobaciones: list[AprobacionResponse]

    @classmethod
    def from_dto(cls, dto: SolicitudDTO) -> "SolicitudResponse":
        s = dto.solicitud
        return cls(
            id=s.id,
            empleado_id=s.empleado_id,
            empleado_nombre=dto.empleado_nombre,
            empleado_color=dto.empleado_color,
            sector_nombre=dto.sector_nombre,
            sector_color=dto.sector_color,
            start_date=s.start_date,
            end_date=s.end_date,
            days_requested=s.days_requested,
            charged_to_year=s.charged_to_year,
            reason=s.reason,
            status=s.status.value,
            created_at=s.created_at,
            aprobaciones=[AprobacionResponse.from_dto(a) for a in dto.aprobaciones],
        )


class AfectaTurnosResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: uuid.UUID = Field(serialization_alias="userId")
    desde: date
    hasta: date

    @classmethod
    def from_dto(cls, dto: AfectaTurnosAviso) -> "AfectaTurnosResponse":
        return cls(user_id=dto.user_id, desde=dto.desde, hasta=dto.hasta)


class DecisionResponse(SolicitudResponse):
    """`SolicitudResponse` + aviso de impacto en turnos (ADR-025). Aditivo:
    `null` cuando se rechaza o el empleado no tiene turnos en el rango."""

    afecta_turnos: AfectaTurnosResponse | None = Field(
        default=None, serialization_alias="afectaTurnos"
    )

    @classmethod
    def from_decision(
        cls, solicitud: SolicitudDTO, afecta: AfectaTurnosAviso | None
    ) -> "DecisionResponse":
        base = SolicitudResponse.from_dto(solicitud)
        return cls(
            **base.model_dump(),
            afecta_turnos=AfectaTurnosResponse.from_dto(afecta) if afecta else None,
        )


class SolapamientosResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    overlaps: list[SolicitudResponse]
    team_size: int = Field(serialization_alias="teamSize")

    @classmethod
    def from_dto(cls, dto: SolapamientosDTO) -> "SolapamientosResponse":
        return cls(
            overlaps=[SolicitudResponse.from_dto(o) for o in dto.overlaps],
            team_size=dto.team_size,
        )


class _RangoBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    charged_to_year: int | None = Field(default=None, alias="chargedToYear")
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _rango_valido(self) -> "_RangoBase":
        if self.end_date < self.start_date:
            raise ValueError("La fecha de fin debe ser posterior o igual a la de inicio")
        return self


class CrearSolicitudRequest(_RangoBase):
    empleado_id: uuid.UUID | None = Field(default=None, alias="empleadoId")

    def to_command(self) -> CrearSolicitudCommand:
        return CrearSolicitudCommand(
            start_date=self.start_date,
            end_date=self.end_date,
            empleado_id=self.empleado_id,
            charged_to_year=self.charged_to_year,
            reason=self.reason,
        )


class EditarSolicitudRequest(_RangoBase):
    def to_command(self) -> EditarSolicitudCommand:
        return EditarSolicitudCommand(
            start_date=self.start_date,
            end_date=self.end_date,
            charged_to_year=self.charged_to_year,
            reason=self.reason,
        )


class DecisionRequest(BaseModel):
    decision: Decision
    comment: str | None = Field(default=None, max_length=500)

    def to_command(self) -> DecidirSolicitudCommand:
        return DecidirSolicitudCommand(decision=self.decision.value, comment=self.comment)
