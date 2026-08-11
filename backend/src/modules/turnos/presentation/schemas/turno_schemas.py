import uuid
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field

from src.modules.turnos.application.dtos.turno_dtos import (
    AsignacionDTO,
    CasillaDTO,
    OperatorShiftView,
    ResolvedShiftDTO,
    SlotDTO,
)
from src.modules.turnos.domain.repositories.user_provider import UserInfo


class OperatorShiftResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: uuid.UUID = Field(serialization_alias="userId")
    user_name: str = Field(serialization_alias="userName")
    color: str | None = None

    @classmethod
    def from_dto(cls, dto: OperatorShiftView) -> "OperatorShiftResponse":
        return cls(user_id=dto.user_id, user_name=dto.user_name, color=dto.color)


class ResolvedShiftResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slot_id: uuid.UUID = Field(serialization_alias="slotId")
    casilla_id: uuid.UUID = Field(serialization_alias="casillaId")
    casilla_nombre: str = Field(serialization_alias="casillaNombre")
    casilla_color: str | None = Field(serialization_alias="casillaColor")
    hora_inicio: time = Field(serialization_alias="horaInicio")
    hora_fin: time = Field(serialization_alias="horaFin")
    dia_semana: int = Field(serialization_alias="diaSemana")
    operadores: list[OperatorShiftResponse]
    is_current: bool = Field(serialization_alias="isCurrent")
    is_next: bool = Field(serialization_alias="isNext")

    @classmethod
    def from_dto(cls, dto: ResolvedShiftDTO) -> "ResolvedShiftResponse":
        return cls(
            slot_id=dto.slot_id,
            casilla_id=dto.casilla_id,
            casilla_nombre=dto.casilla_nombre,
            casilla_color=dto.casilla_color,
            hora_inicio=dto.hora_inicio,
            hora_fin=dto.hora_fin,
            dia_semana=dto.dia_semana,
            operadores=[OperatorShiftResponse.from_dto(op) for op in dto.operadores],
            is_current=dto.is_current,
            is_next=dto.is_next,
        )


class CasillaRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nombre: str
    color: str | None = None
    sort_order: int = Field(
        default=0, validation_alias="sortOrder", serialization_alias="sortOrder"
    )
    is_active: bool = Field(
        default=True, validation_alias="isActive", serialization_alias="isActive"
    )


class CasillaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    nombre: str
    color: str | None
    sort_order: int = Field(serialization_alias="sortOrder")
    is_active: bool = Field(serialization_alias="isActive")

    @classmethod
    def from_dto(cls, dto: CasillaDTO) -> "CasillaResponse":
        return cls(
            id=dto.id,
            nombre=dto.nombre,
            color=dto.color,
            sort_order=dto.sort_order,
            is_active=dto.is_active,
        )


class AsignacionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    slot_id: uuid.UUID = Field(serialization_alias="slotId")
    user_id: uuid.UUID = Field(serialization_alias="userId")
    user_name: str | None = Field(serialization_alias="userName")
    vigente_desde: date = Field(serialization_alias="vigenteDesde")
    vigente_hasta: date | None = Field(serialization_alias="vigenteHasta")

    @classmethod
    def from_dto(cls, dto: AsignacionDTO) -> "AsignacionResponse":
        return cls(
            id=dto.id,
            slot_id=dto.slot_id,
            user_id=dto.user_id,
            user_name=dto.user_name,
            vigente_desde=dto.vigente_desde,
            vigente_hasta=dto.vigente_hasta,
        )


class SlotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    casilla_id: uuid.UUID = Field(validation_alias="casillaId", serialization_alias="casillaId")
    hora_inicio: time = Field(validation_alias="horaInicio", serialization_alias="horaInicio")
    hora_fin: time = Field(validation_alias="horaFin", serialization_alias="horaFin")
    dia_semana: int = Field(validation_alias="diaSemana", serialization_alias="diaSemana")
    sort_order: int = Field(
        default=0, validation_alias="sortOrder", serialization_alias="sortOrder"
    )


class SlotResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    casilla_id: uuid.UUID = Field(serialization_alias="casillaId")
    hora_inicio: time = Field(serialization_alias="horaInicio")
    hora_fin: time = Field(serialization_alias="horaFin")
    dia_semana: int = Field(serialization_alias="diaSemana")
    sort_order: int = Field(serialization_alias="sortOrder")
    asignaciones: list[AsignacionResponse]

    @classmethod
    def from_dto(cls, dto: SlotDTO) -> "SlotResponse":
        return cls(
            id=dto.id,
            casilla_id=dto.casilla_id,
            hora_inicio=dto.hora_inicio,
            hora_fin=dto.hora_fin,
            dia_semana=dto.dia_semana,
            sort_order=dto.sort_order,
            asignaciones=[AsignacionResponse.from_dto(a) for a in dto.asignaciones],
        )


class ReplaceAssignmentsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_ids: list[uuid.UUID] = Field(validation_alias="userIds", serialization_alias="userIds")
    vigente_desde: date = Field(validation_alias="vigenteDesde", serialization_alias="vigenteDesde")


class UserOptionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    full_name: str = Field(serialization_alias="fullName")

    @classmethod
    def from_info(cls, info: UserInfo) -> "UserOptionResponse":
        return cls(id=info.id, full_name=info.full_name)
