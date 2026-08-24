import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vacaciones.application.dtos.siges_vinculo_dtos import (
    PropuestasVinculoEmpleadoResultado,
    PropuestaVinculoEmpleado,
    SigesTecnicoDisponibleDTO,
)


class PropuestaVinculoEmpleadoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    empleado_id: uuid.UUID = Field(serialization_alias="empleadoId")
    empleado_nombre: str = Field(serialization_alias="empleadoNombre")
    siges_empresa_id: int = Field(serialization_alias="sigesEmpresaId")
    siges_den_comercial: str = Field(serialization_alias="sigesDenComercial")

    @classmethod
    def from_dto(cls, dto: PropuestaVinculoEmpleado) -> "PropuestaVinculoEmpleadoResponse":
        return cls(
            empleado_id=dto.empleado_id,
            empleado_nombre=dto.empleado_nombre,
            siges_empresa_id=dto.siges_empresa_id,
            siges_den_comercial=dto.siges_den_comercial,
        )


class SigesTecnicoDisponibleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    siges_empresa_id: int = Field(serialization_alias="sigesEmpresaId")
    den_comercial: str = Field(serialization_alias="denComercial")

    @classmethod
    def from_dto(cls, dto: SigesTecnicoDisponibleDTO) -> "SigesTecnicoDisponibleResponse":
        return cls(siges_empresa_id=dto.siges_empresa_id, den_comercial=dto.den_comercial)


class PropuestasVinculoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    propuestas: list[PropuestaVinculoEmpleadoResponse]
    disponibles: list[SigesTecnicoDisponibleResponse]

    @classmethod
    def from_resultado(
        cls, resultado: PropuestasVinculoEmpleadoResultado
    ) -> "PropuestasVinculoResponse":
        return cls(
            propuestas=[PropuestaVinculoEmpleadoResponse.from_dto(p) for p in resultado.propuestas],
            disponibles=[
                SigesTecnicoDisponibleResponse.from_dto(d) for d in resultado.disponibles
            ],
        )


class VincularSigesIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    siges_empresa_id: int | None = Field(alias="sigesEmpresaId")
