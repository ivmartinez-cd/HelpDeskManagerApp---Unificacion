import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.modules.prestadores.application.dtos.prestador_dtos import (
    AsignacionHistorialDTO,
    ContactoDTO,
    OperadorGroupDTO,
    PrestadorDTO,
    PrestadoresResumenDTO,
    SyncResultDTO,
)
from src.modules.prestadores.domain.repositories.user_provider import UserInfo


class ContactoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    nombre: str
    telefono: str | None
    email: str | None
    is_principal: bool = Field(serialization_alias="isPrincipal")
    sort_order: int = Field(serialization_alias="sortOrder")

    @classmethod
    def from_dto(cls, dto: ContactoDTO) -> "ContactoResponse":
        return cls(
            id=dto.id,
            prestador_id=dto.prestador_id,
            nombre=dto.nombre,
            telefono=dto.telefono,
            email=dto.email,
            is_principal=dto.is_principal,
            sort_order=dto.sort_order,
        )


class PrestadorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    siges_empresa_id: int = Field(serialization_alias="sigesEmpresaId")
    den_comercial: str = Field(serialization_alias="denComercial")
    razon_social: str | None = Field(serialization_alias="razonSocial")
    cuit: str | None
    operador_id: uuid.UUID | None = Field(serialization_alias="operadorId")
    operador_nombre: str | None = Field(serialization_alias="operadorNombre")
    operador_color: str | None = Field(serialization_alias="operadorColor")
    is_active: bool = Field(serialization_alias="isActive")
    contactos: list[ContactoResponse]

    @classmethod
    def from_dto(cls, dto: PrestadorDTO) -> "PrestadorResponse":
        return cls(
            id=dto.id,
            siges_empresa_id=dto.siges_empresa_id,
            den_comercial=dto.den_comercial,
            razon_social=dto.razon_social,
            cuit=dto.cuit,
            operador_id=dto.operador_id,
            operador_nombre=dto.operador_nombre,
            operador_color=dto.operador_color,
            is_active=dto.is_active,
            contactos=[ContactoResponse.from_dto(c) for c in dto.contactos],
        )


class OperadorGroupResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    operador_id: uuid.UUID | None = Field(serialization_alias="operadorId")
    operador_nombre: str | None = Field(serialization_alias="operadorNombre")
    operador_color: str | None = Field(serialization_alias="operadorColor")
    prestadores: list[PrestadorResponse]

    @classmethod
    def from_dto(cls, dto: OperadorGroupDTO) -> "OperadorGroupResponse":
        return cls(
            operador_id=dto.operador_id,
            operador_nombre=dto.operador_nombre,
            operador_color=dto.operador_color,
            prestadores=[PrestadorResponse.from_dto(p) for p in dto.prestadores],
        )


class PrestadoresResumenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_prestadores: int = Field(serialization_alias="totalPrestadores")
    total_activos: int = Field(serialization_alias="totalActivos")
    operadores_con_pst: int = Field(serialization_alias="operadoresConPst")
    sin_asignar: int = Field(serialization_alias="sinAsignar")
    grupos: list[OperadorGroupResponse]

    @classmethod
    def from_dto(cls, dto: PrestadoresResumenDTO) -> "PrestadoresResumenResponse":
        return cls(
            total_prestadores=dto.total_prestadores,
            total_activos=dto.total_activos,
            operadores_con_pst=dto.operadores_con_pst,
            sin_asignar=dto.sin_asignar,
            grupos=[OperadorGroupResponse.from_dto(g) for g in dto.grupos],
        )


class CreatePrestadorRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    siges_empresa_id: int = Field(validation_alias="sigesEmpresaId")
    den_comercial: str = Field(validation_alias="denComercial")
    razon_social: str | None = Field(default=None, validation_alias="razonSocial")
    cuit: str | None = None
    operador_id: uuid.UUID | None = Field(default=None, validation_alias="operadorId")


class UpdatePrestadorRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    den_comercial: str = Field(validation_alias="denComercial")
    razon_social: str | None = Field(default=None, validation_alias="razonSocial")
    cuit: str | None = None


class SetActiveRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    is_active: bool = Field(validation_alias="isActive")


class AssignOperadorRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    operador_id: uuid.UUID | None = Field(validation_alias="operadorId")
    desde: date


class UpsertContactoRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nombre: str
    telefono: str | None = None
    email: str | None = None
    is_principal: bool = Field(default=False, validation_alias="isPrincipal")
    sort_order: int = Field(default=0, validation_alias="sortOrder")


class AsignacionHistorialResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    operador_id: uuid.UUID | None = Field(serialization_alias="operadorId")
    operador_nombre: str | None = Field(serialization_alias="operadorNombre")
    desde: date
    hasta: date | None

    @classmethod
    def from_dto(cls, dto: AsignacionHistorialDTO) -> "AsignacionHistorialResponse":
        return cls(
            id=dto.id,
            operador_id=dto.operador_id,
            operador_nombre=dto.operador_nombre,
            desde=dto.desde,
            hasta=dto.hasta,
        )


class SyncResultResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    actualizados: list[str]
    sin_cambios: int = Field(serialization_alias="sinCambios")

    @classmethod
    def from_dto(cls, dto: SyncResultDTO) -> "SyncResultResponse":
        return cls(actualizados=dto.actualizados, sin_cambios=dto.sin_cambios)


class OperadorOptionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    full_name: str = Field(serialization_alias="fullName")
    color: str | None = None

    @classmethod
    def from_info(cls, info: UserInfo) -> "OperadorOptionResponse":
        return cls(id=info.id, full_name=info.full_name, color=info.color)
