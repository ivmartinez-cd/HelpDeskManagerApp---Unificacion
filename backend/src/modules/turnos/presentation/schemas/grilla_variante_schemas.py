import uuid
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field

from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    AdvertenciaCoberturaDTO,
    GrillaVarianteDTO,
    PrecargaGrillaDTO,
    PrecargaSlotDTO,
    VarianteActivaDTO,
    VarianteSlotDTO,
    VarianteSlotInput,
)
from src.modules.turnos.presentation.schemas.turno_schemas import (
    OperatorShiftResponse,
    ResolvedShiftResponse,
)
from src.shared.presentation.schemas.pagination import Page


class VarianteSlotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    casilla_id: uuid.UUID = Field(validation_alias="casillaId")
    dia_semana: int = Field(validation_alias="diaSemana", ge=0, le=6)
    hora_inicio: time = Field(validation_alias="horaInicio")
    hora_fin: time = Field(validation_alias="horaFin")
    user_ids: list[uuid.UUID] = Field(default_factory=list, validation_alias="userIds")

    def to_input(self) -> VarianteSlotInput:
        return VarianteSlotInput(
            casilla_id=self.casilla_id,
            dia_semana=self.dia_semana,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
            user_ids=self.user_ids,
        )


class GrillaVarianteRequest(BaseModel):
    """Mismo body para alta (POST) y edición (PUT): el id va en el path."""

    model_config = ConfigDict(populate_by_name=True)

    motivo: str | None = Field(default=None, max_length=200)
    origen_texto: str | None = Field(
        default=None, max_length=200, validation_alias="origenTexto"
    )
    desde: date
    hasta: date
    slots: list[VarianteSlotRequest]


class AdvertenciaCoberturaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tipo: str
    casilla_id: uuid.UUID | None = Field(default=None, serialization_alias="casillaId")
    casilla_nombre: str | None = Field(default=None, serialization_alias="casillaNombre")
    dia_semana: int | None = Field(default=None, serialization_alias="diaSemana")
    hora_inicio: time | None = Field(default=None, serialization_alias="horaInicio")
    hora_fin: time | None = Field(default=None, serialization_alias="horaFin")
    user_id: uuid.UUID | None = Field(default=None, serialization_alias="userId")
    user_name: str | None = Field(default=None, serialization_alias="userName")
    desde: date | None = None
    hasta: date | None = None

    @classmethod
    def from_dto(cls, dto: AdvertenciaCoberturaDTO) -> "AdvertenciaCoberturaResponse":
        return cls(
            tipo=dto.tipo,
            casilla_id=dto.casilla_id,
            casilla_nombre=dto.casilla_nombre,
            dia_semana=dto.dia_semana,
            hora_inicio=dto.hora_inicio,
            hora_fin=dto.hora_fin,
            user_id=dto.user_id,
            user_name=dto.user_name,
            desde=dto.desde,
            hasta=dto.hasta,
        )


class VarianteSlotResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    casilla_id: uuid.UUID = Field(serialization_alias="casillaId")
    casilla_nombre: str = Field(serialization_alias="casillaNombre")
    dia_semana: int = Field(serialization_alias="diaSemana")
    hora_inicio: time = Field(serialization_alias="horaInicio")
    hora_fin: time = Field(serialization_alias="horaFin")
    sort_order: int = Field(serialization_alias="sortOrder")
    operadores: list[OperatorShiftResponse]

    @classmethod
    def from_dto(cls, dto: VarianteSlotDTO) -> "VarianteSlotResponse":
        return cls(
            id=dto.id,
            casilla_id=dto.casilla_id,
            casilla_nombre=dto.casilla_nombre,
            dia_semana=dto.dia_semana,
            hora_inicio=dto.hora_inicio,
            hora_fin=dto.hora_fin,
            sort_order=dto.sort_order,
            operadores=[OperatorShiftResponse.from_dto(o) for o in dto.operadores],
        )


class GrillaVarianteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    motivo: str | None
    origen_texto: str | None = Field(serialization_alias="origenTexto")
    desde: date
    hasta: date
    estado: str
    created_by_user_id: uuid.UUID = Field(serialization_alias="createdByUserId")
    slots: list[VarianteSlotResponse]
    advertencias: list[AdvertenciaCoberturaResponse]

    @classmethod
    def from_dto(cls, dto: GrillaVarianteDTO) -> "GrillaVarianteResponse":
        return cls(
            id=dto.id,
            motivo=dto.motivo,
            origen_texto=dto.origen_texto,
            desde=dto.desde,
            hasta=dto.hasta,
            estado=dto.estado,
            created_by_user_id=dto.created_by_user_id,
            slots=[VarianteSlotResponse.from_dto(s) for s in dto.slots],
            advertencias=[AdvertenciaCoberturaResponse.from_dto(a) for a in dto.advertencias],
        )


class PrecargaSlotResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    casilla_id: uuid.UUID = Field(serialization_alias="casillaId")
    casilla_nombre: str = Field(serialization_alias="casillaNombre")
    dia_semana: int = Field(serialization_alias="diaSemana")
    hora_inicio: time = Field(serialization_alias="horaInicio")
    hora_fin: time = Field(serialization_alias="horaFin")
    sort_order: int = Field(serialization_alias="sortOrder")
    operadores: list[OperatorShiftResponse]
    requiere_cobertura: bool = Field(serialization_alias="requiereCobertura")

    @classmethod
    def from_dto(cls, dto: PrecargaSlotDTO) -> "PrecargaSlotResponse":
        return cls(
            casilla_id=dto.casilla_id,
            casilla_nombre=dto.casilla_nombre,
            dia_semana=dto.dia_semana,
            hora_inicio=dto.hora_inicio,
            hora_fin=dto.hora_fin,
            sort_order=dto.sort_order,
            operadores=[OperatorShiftResponse.from_dto(o) for o in dto.operadores],
            requiere_cobertura=dto.requiere_cobertura,
        )


class PrecargaGrillaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ausente_user_id: uuid.UUID = Field(serialization_alias="ausenteUserId")
    ausente_nombre: str | None = Field(serialization_alias="ausenteNombre")
    desde: date
    hasta: date
    slots: list[PrecargaSlotResponse]
    advertencias: list[AdvertenciaCoberturaResponse]

    @classmethod
    def from_dto(cls, dto: PrecargaGrillaDTO) -> "PrecargaGrillaResponse":
        return cls(
            ausente_user_id=dto.ausente_user_id,
            ausente_nombre=dto.ausente_nombre,
            desde=dto.desde,
            hasta=dto.hasta,
            slots=[PrecargaSlotResponse.from_dto(s) for s in dto.slots],
            advertencias=[AdvertenciaCoberturaResponse.from_dto(a) for a in dto.advertencias],
        )


class VarianteActivaResponse(BaseModel):
    id: uuid.UUID
    motivo: str | None
    desde: date
    hasta: date

    @classmethod
    def from_dto(cls, dto: VarianteActivaDTO) -> "VarianteActivaResponse":
        return cls(id=dto.id, motivo=dto.motivo, desde=dto.desde, hasta=dto.hasta)


class CurrentShiftsResponse(Page[ResolvedShiftResponse]):
    """`Page[ResolvedShiftResponse]` + la cabecera de la grilla de vacaciones
    vigente hoy (ADR-025). Aditivo: `items/total/page/size` no cambian."""

    model_config = ConfigDict(populate_by_name=True)

    variante_activa: VarianteActivaResponse | None = Field(
        default=None, serialization_alias="varianteActiva"
    )
