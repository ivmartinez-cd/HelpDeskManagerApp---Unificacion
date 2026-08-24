import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.modules.vacaciones.application.dtos.gestion_dtos import (
    EmpleadoCommand,
    EmpleadoListItemDTO,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.presentation.schemas.dashboard_schemas import SaldoResponse


class EmpleadoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    first_name: str = Field(serialization_alias="firstName")
    last_name: str = Field(serialization_alias="lastName")
    email: str
    hire_date: date = Field(serialization_alias="hireDate")
    status: str
    color: str
    department_id: uuid.UUID = Field(serialization_alias="departmentId")
    cargo_id: uuid.UUID = Field(serialization_alias="cargoId")
    user_id: uuid.UUID | None = Field(serialization_alias="userId")
    siges_empresa_id: int | None = Field(serialization_alias="sigesEmpresaId")

    @classmethod
    def from_entity(cls, empleado: Empleado) -> "EmpleadoResponse":
        return cls(
            id=empleado.id,
            first_name=empleado.first_name,
            last_name=empleado.last_name,
            email=empleado.email,
            hire_date=empleado.hire_date,
            status=empleado.status.value,
            color=empleado.color,
            department_id=empleado.department_id,
            cargo_id=empleado.cargo_id,
            user_id=empleado.user_id,
            siges_empresa_id=empleado.siges_empresa_id,
        )


class EmpleadoListItemResponse(EmpleadoResponse):
    sector_nombre: str = Field(serialization_alias="sectorNombre")
    sector_color: str = Field(serialization_alias="sectorColor")
    cargo_nombre: str = Field(serialization_alias="cargoNombre")
    dias_anuales: int = Field(serialization_alias="diasAnuales")
    antiguedad_anios: float = Field(serialization_alias="antiguedadAnios")
    saldo: SaldoResponse
    saldo_siguiente: SaldoResponse | None = Field(serialization_alias="saldoSiguiente")

    @classmethod
    def from_dto(cls, dto: EmpleadoListItemDTO) -> "EmpleadoListItemResponse":
        base = EmpleadoResponse.from_entity(dto.empleado)
        return cls(
            **base.model_dump(by_alias=False),
            sector_nombre=dto.sector_nombre,
            sector_color=dto.sector_color,
            cargo_nombre=dto.cargo_nombre,
            dias_anuales=dto.dias_anuales,
            antiguedad_anios=round(dto.antiguedad_anios, 2),
            saldo=SaldoResponse.from_saldo(dto.saldo),
            saldo_siguiente=(
                SaldoResponse.from_saldo(dto.saldo_siguiente)
                if dto.saldo_siguiente
                else None
            ),
        )


class EmpleadoRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(alias="firstName", min_length=1, max_length=100)
    last_name: str = Field(alias="lastName", min_length=1, max_length=100)
    email: EmailStr
    hire_date: date = Field(alias="hireDate")
    department_id: uuid.UUID = Field(alias="departmentId")
    cargo_id: uuid.UUID = Field(alias="cargoId")
    color: str = Field(default="#3b82f6", max_length=20)
    status: EstadoEmpleado = EstadoEmpleado.ACTIVE
    user_id: uuid.UUID | None = Field(default=None, alias="userId")

    def to_command(self) -> EmpleadoCommand:
        return EmpleadoCommand(
            first_name=self.first_name,
            last_name=self.last_name,
            email=str(self.email),
            hire_date=self.hire_date,
            department_id=self.department_id,
            cargo_id=self.cargo_id,
            color=self.color,
            status=self.status,
            user_id=self.user_id,
        )
